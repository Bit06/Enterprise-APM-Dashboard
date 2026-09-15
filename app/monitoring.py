"""
Monitoring Engine + Data Collection Layer.

Periodically probes every active endpoint, records HTTP status code,
response time and availability into the database, and hands off to the
alerting service to evaluate whether a notification is needed.
"""
import time
import logging
import requests
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

from .database import SessionLocal
from .models import Endpoint, MonitoringResult
from .worker import telemetry_queue

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("apm.monitoring")

scheduler = BackgroundScheduler()

import math

def probe_endpoint(endpoint: Endpoint) -> dict:
    """Perform a single HTTP probe against an endpoint. This is the
    'data collection' step: it captures status code, response time,
    and availability, along with simulated server resource utilization."""
    start = time.time()
    
    res = {
        "status_code": None,
        "response_time_ms": None,
        "is_available": False,
        "error_message": None,
    }
    
    try:
        response = requests.get(endpoint.url, timeout=endpoint.timeout_seconds)
        elapsed_ms = (time.time() - start) * 1000
        res["status_code"] = response.status_code
        res["response_time_ms"] = round(elapsed_ms, 2)
        res["is_available"] = response.status_code < 400
    except requests.exceptions.Timeout:
        res["error_message"] = "Request timed out"
    except requests.exceptions.ConnectionError as e:
        res["error_message"] = f"Connection error: {e}"
    except requests.exceptions.RequestException as e:
        res["error_message"] = str(e)
        
    # Simulate Server Resource Utilization
    now_ts = time.time()
    # Deterministic noise based on time (10-minute cycle)
    noise = math.sin(now_ts / 600.0 * math.pi * 2 + endpoint.id)
    # Memory: 24-hour cycle from 40% to 80%
    memory_percent = 60 + 20 * math.sin(now_ts / 86400.0 * math.pi * 2 + endpoint.id * 10) + (noise * 2)
    # CPU: base 20-30%
    cpu_percent = 25 + (noise * 5)
    
    if not res["is_available"]:
        # Service dead -> no CPU usage
        cpu_percent = 2.0 + abs(noise)
    else:
        rt = res["response_time_ms"] or 0
        if rt > endpoint.response_time_warn_ms * 0.5:
            # Spike CPU when response time is high
            cpu_percent += min(70, (rt / 10.0))
            
    res["server_cpu_percent"] = round(max(0.1, min(99.9, cpu_percent)), 1)
    res["server_memory_percent"] = round(max(10.0, min(99.9, memory_percent)), 1)
    
    return res

def run_check(endpoint_id: int):
    """Runs one probe cycle for a single endpoint and publishes the result to the queue."""
    db = SessionLocal()
    try:
        endpoint = db.query(Endpoint).filter(Endpoint.id == endpoint_id).first()
        if not endpoint or not endpoint.is_active:
            return

        result_data = probe_endpoint(endpoint)

        # Decouple: Publish to the queue instead of processing synchronously
        telemetry_queue.put({
            "endpoint_id": endpoint.id,
            "result_data": result_data
        })
        logger.info(f"Published telemetry for {endpoint.name} to the queue.")

    finally:
        db.close()


def schedule_endpoint(endpoint: Endpoint):
    """Registers (or re-registers) a recurring job for one endpoint."""
    job_id = f"endpoint_{endpoint.id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    scheduler.add_job(
        run_check,
        "interval",
        seconds=endpoint.check_interval_seconds,
        args=[endpoint.id],
        id=job_id,
        next_run_time=datetime.utcnow(),  # run immediately on registration
        max_instances=1,
        coalesce=True,
    )


def unschedule_endpoint(endpoint_id: int):
    job_id = f"endpoint_{endpoint_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)


def start_scheduler():
    """Loads all active endpoints from the DB and schedules their checks.
    Call once on application startup."""
    db = SessionLocal()
    try:
        endpoints = db.query(Endpoint).filter(Endpoint.is_active == True).all()  # noqa: E712
        for ep in endpoints:
            schedule_endpoint(ep)
        
        # Schedule ML model training
        from .ml_engine import train_anomaly_models
        if scheduler.get_job("ml_training"):
            scheduler.remove_job("ml_training")
        scheduler.add_job(
            train_anomaly_models,
            "interval",
            minutes=5,
            id="ml_training",
            next_run_time=datetime.utcnow() # Run immediately to train models on startup
        )
        
        # Schedule Metric Aggregation
        if scheduler.get_job("aggregate_metrics"):
            scheduler.remove_job("aggregate_metrics")
        scheduler.add_job(
            aggregate_metrics,
            "interval",
            minutes=1,
            id="aggregate_metrics",
            next_run_time=datetime.utcnow() + timedelta(minutes=1)
        )
        
        if not scheduler.running:
            scheduler.start()
        logger.info("Scheduler started with %d active endpoint(s) and ML training job.", len(endpoints))
    finally:
        db.close()

def aggregate_metrics():
    """Aggregates raw RequestLogs from the last minute into MetricBucket."""
    db = SessionLocal()
    try:
        now_ts = time.time()
        current_minute_ts = now_ts - (now_ts % 60)
        last_minute_ts = current_minute_ts - 60
        last_minute_dt = datetime.utcfromtimestamp(last_minute_ts)
        
        from .models import RequestLog, MetricBucket
        
        logs = db.query(RequestLog).filter(
            RequestLog.timestamp >= last_minute_ts,
            RequestLog.timestamp < current_minute_ts
        ).all()
        logs = db.query(RequestLog).filter(
            RequestLog.timestamp >= last_minute_ts,
            RequestLog.timestamp < current_minute_ts
        ).all()
        
        if not logs:
            return
            
        groups = {}
        for log in logs:
            key = (log.endpoint, log.method)
            if key not in groups:
                groups[key] = []
            groups[key].append(log)
            
        buckets = []
        for (ep, method), group_logs in groups.items():
            count = len(group_logs)
            rps = count / 60.0
            error_count = sum(1 for l in group_logs if l.status_code >= 500)
            error_rate = (error_count / count) * 100.0 if count > 0 else 0.0
            
            durations = sorted([l.duration_ms for l in group_logs])
            p50 = durations[int(0.50 * len(durations))] if durations else 0.0
            p95 = durations[int(0.95 * len(durations))] if durations else 0.0
            p99 = durations[int(0.99 * len(durations))] if durations else 0.0
            
            # Detect anomaly using ML engine
            try:
                from .ml_engine import detect_anomaly
                is_anomaly, score, label = detect_anomaly(ep, p99)
            except Exception as e:
                logger.error(f"Error detecting anomaly: {e}")
                is_anomaly, score, label = False, 0.0, None
                
            bucket = MetricBucket(
                endpoint=ep,
                method=method,
                bucket_minute=last_minute_dt,
                request_count=count,
                error_count=error_count,
                error_rate=error_rate,
                rps=rps,
                p50_latency_ms=p50,
                p95_latency_ms=p95,
                p99_latency_ms=p99,
                is_anomaly=is_anomaly,
                anomaly_label=label
            )
            buckets.append(bucket)
            
        db.add_all(buckets)
        db.commit()
        logger.info(f"Aggregated {len(logs)} logs into {len(buckets)} MetricBuckets.")
        
        # Evaluate SLO alerts after aggregation
        try:
            from .alerts import evaluate_slo_alerts
            evaluate_slo_alerts(db)
        except Exception as e:
            logger.error(f"Failed to evaluate SLO alerts: {e}")
            
        # Cleanup processed raw logs to save space
        db.query(RequestLog).filter(RequestLog.timestamp < current_minute_ts).delete()
        db.commit()
    finally:
        db.close()


def cleanup_old_results(retention_days: int = 30):
    """Optional housekeeping job: purge monitoring_results older than N days
    to keep the database size manageable. Schedule this separately if desired."""
    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(days=retention_days)
        deleted = db.query(MonitoringResult).filter(MonitoringResult.timestamp < cutoff).delete()
        db.commit()
        logger.info("Purged %d monitoring results older than %d days.", deleted, retention_days)
    finally:
        db.close()
