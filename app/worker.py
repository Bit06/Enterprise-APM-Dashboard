import threading
import queue
import logging
from datetime import datetime
from .database import SessionLocal
from .models import Endpoint, MonitoringResult, EndpointInterval
from .alerts import evaluate_alerts

logger = logging.getLogger("apm.worker")

# The in-memory message broker (simulating Kafka/Redis for the prototype)
telemetry_queue = queue.Queue()

def process_telemetry():
    """Background worker that continuously consumes telemetry from the queue
    and processes it (saving to DB, triggering alerts, running ML inference)."""
    logger.info("Telemetry worker started. Listening for messages...")
    while True:
        try:
            # Block until an item is available
            message = telemetry_queue.get()
            if message is None:
                break  # Poison pill to stop the thread
            
            endpoint_id = message["endpoint_id"]
            result_data = message["result_data"]
            
            db = SessionLocal()
            try:
                endpoint = db.query(Endpoint).filter(Endpoint.id == endpoint_id).first()
                if not endpoint or not endpoint.is_active:
                    continue

                # Run multivariate ML anomaly detection
                from .ml_engine import detect_anomaly
                features = {
                    "response_time_ms": result_data.get("response_time_ms") or 0.0,
                    "p95_latency_ms": result_data.get("response_time_ms") or 0.0,
                    "p99_latency_ms": result_data.get("response_time_ms") or 0.0,
                    "server_cpu_percent": result_data.get("server_cpu_percent", 25.0),
                    "server_memory_percent": result_data.get("server_memory_percent", 60.0),
                    "error_rate": 100.0 if not result_data.get("is_available") else 0.0,
                    "rps": 1.0
                }
                anomaly_res = detect_anomaly(endpoint.id, features)
                is_anomaly = anomaly_res[0]
                anomaly_score = anomaly_res[1]

                # 1. Save telemetry to time-series DB (simulated by SQLite here)
                now_utc = datetime.utcnow()
                result = MonitoringResult(
                    endpoint_id=endpoint.id,
                    timestamp=now_utc,
                    is_anomaly=is_anomaly,
                    anomaly_score=anomaly_score,
                    **result_data,
                )
                db.add(result)
                
                # 1b. Update Pre-computed Endpoint Intervals
                current_status = 'up' if result.is_available else 'down'
                last_interval = db.query(EndpointInterval).filter(
                    EndpointInterval.endpoint_id == endpoint.id
                ).order_by(EndpointInterval.start_time.desc()).first()

                if not last_interval:
                    db.add(EndpointInterval(
                        endpoint_id=endpoint.id,
                        status=current_status,
                        start_time=now_utc,
                        end_time=now_utc,
                        duration_seconds=0.0
                    ))
                elif last_interval.status == current_status:
                    last_interval.end_time = now_utc
                    last_interval.duration_seconds = (now_utc - last_interval.start_time).total_seconds()
                else:
                    db.add(EndpointInterval(
                        endpoint_id=endpoint.id,
                        status=current_status,
                        start_time=now_utc,
                        end_time=now_utc,
                        duration_seconds=0.0
                    ))

                db.commit()
                db.refresh(result)

                logger.info(
                    "Processed telemetry for %s -> available=%s status=%s time=%sms",
                    endpoint.name, result.is_available, result.status_code, result.response_time_ms
                )

                # 2. Evaluate Alerts (which will later include ML anomaly flags)
                evaluate_alerts(db, endpoint, result)
            finally:
                db.close()
            
            telemetry_queue.task_done()
        except Exception as e:
            logger.error(f"Error processing telemetry: {e}")

# Start the worker thread
worker_thread = threading.Thread(target=process_telemetry, daemon=True)

def start_worker():
    if not worker_thread.is_alive():
        worker_thread.start()
