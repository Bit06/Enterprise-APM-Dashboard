from datetime import datetime, timedelta
from typing import List

from fastapi import FastAPI, Depends, HTTPException, Query, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from . import models, schemas
from .database import engine, get_db, Base
from .monitoring import start_scheduler, schedule_endpoint, unschedule_endpoint
from .worker import start_worker

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Enterprise API & Application Performance Monitoring System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    start_scheduler()
    start_worker()


# ---------- Endpoint registry ----------

@app.post("/api/endpoints", response_model=schemas.EndpointOut)
def create_endpoint(payload: schemas.EndpointCreate, db: Session = Depends(get_db)):
    endpoint = models.Endpoint(**payload.model_dump())
    db.add(endpoint)
    db.commit()
    db.refresh(endpoint)
    schedule_endpoint(endpoint)
    return endpoint


@app.get("/api/endpoints", response_model=List[schemas.EndpointOut])
def list_endpoints(db: Session = Depends(get_db)):
    return db.query(models.Endpoint).all()


@app.delete("/api/endpoints/{endpoint_id}")
def delete_endpoint(endpoint_id: int, db: Session = Depends(get_db)):
    endpoint = db.query(models.Endpoint).filter(models.Endpoint.id == endpoint_id).first()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    unschedule_endpoint(endpoint_id)
    db.delete(endpoint)
    db.commit()
    return {"deleted": True}


# ---------- Live status (dashboard grid) ----------

@app.get("/api/status", response_model=List[schemas.EndpointStatus])
def get_status(db: Session = Depends(get_db)):
    endpoints = db.query(models.Endpoint).filter(models.Endpoint.is_active == True).all()  # noqa: E712
    out = []
    since = datetime.utcnow() - timedelta(hours=24)

    for ep in endpoints:
        latest = (
            db.query(models.MonitoringResult)
            .filter(models.MonitoringResult.endpoint_id == ep.id)
            .order_by(models.MonitoringResult.timestamp.desc())
            .first()
        )

        total_24h = (
            db.query(func.count(models.MonitoringResult.id))
            .filter(models.MonitoringResult.endpoint_id == ep.id, models.MonitoringResult.timestamp >= since)
            .scalar()
        ) or 0
        up_24h = (
            db.query(func.count(models.MonitoringResult.id))
            .filter(
                models.MonitoringResult.endpoint_id == ep.id,
                models.MonitoringResult.timestamp >= since,
                models.MonitoringResult.is_available == True,  # noqa: E712
            )
            .scalar()
        ) or 0
        availability_pct = (up_24h / total_24h * 100) if total_24h else 100.0

        if not latest:
            health = "unknown"
        elif not latest.is_available:
            health = "down"
        elif latest.response_time_ms and latest.response_time_ms >= ep.response_time_warn_ms:
            health = "degraded"
        else:
            health = "up"

        latest_bucket = db.query(models.MetricBucket).filter(
            models.MetricBucket.endpoint.like(f"%{ep.url}%")
        ).order_by(models.MetricBucket.bucket_minute.desc()).first()
        
        slo_data = get_endpoint_slo(ep.id, db)
        burn_rate = slo_data.get("burn_rate", 0.0) if type(slo_data) is dict else 0.0

        out.append(schemas.EndpointStatus(
            endpoint_id=ep.id,
            name=ep.name,
            environment=ep.environment,
            url=ep.url,
            is_available=latest.is_available if latest else False,
            status_code=latest.status_code if latest else None,
            response_time_ms=latest.response_time_ms if latest else None,
            p99_latency_ms=latest_bucket.p99_latency_ms if latest_bucket else None,
            rps=latest_bucket.rps if latest_bucket else None,
            error_rate=latest_bucket.error_rate if latest_bucket else None,
            slo_burn_rate=burn_rate,
            last_checked=latest.timestamp if latest else None,
            health=health,
            availability_pct_24h=round(availability_pct, 2),
        ))
    return out


# ---------- Historical data & Forecasts ----------

@app.get("/api/history/{endpoint_id}", response_model=List[schemas.MonitoringResultOut])
def get_history(endpoint_id: int, hours: float = 24.0, offset_hours: float = 0.0, db: Session = Depends(get_db)):
    until = datetime.utcnow() - timedelta(hours=offset_hours)
    since = until - timedelta(hours=hours)
    results = (
        db.query(models.MonitoringResult)
        .filter(models.MonitoringResult.endpoint_id == endpoint_id,
                models.MonitoringResult.timestamp >= since,
                models.MonitoringResult.timestamp <= until)
        .order_by(models.MonitoringResult.timestamp.asc())
        .all()
    )
    return results


@app.get("/api/forecast/{endpoint_id}", response_model=schemas.ForecastOut)
def get_forecast(endpoint_id: int, steps: int = 10):
    from .ml_engine import generate_forecast
    forecasted_values = generate_forecast(endpoint_id, steps=steps)
    return schemas.ForecastOut(
        endpoint_id=endpoint_id,
        forecasted_response_times=forecasted_values
    )


# ---------- Detailed Endpoint View ----------

@app.get("/api/endpoints/{endpoint_id}/summary")
def get_endpoint_summary(endpoint_id: int, hours: float = 168.0, db: Session = Depends(get_db)):
    since = datetime.utcnow() - timedelta(hours=hours)
    
    # Get all intervals
    intervals = db.query(models.EndpointInterval).filter(
        models.EndpointInterval.endpoint_id == endpoint_id,
        models.EndpointInterval.end_time >= since
    ).all()
    
    downtime_sec = 0.0
    uptime_sec = 0.0
    outages = 0
    
    for iv in intervals:
        start = max(iv.start_time, since)
        end = iv.end_time or datetime.utcnow()
        dur = (end - start).total_seconds()
        if iv.status == 'down':
            downtime_sec += dur
            outages += 1
        else:
            uptime_sec += dur
            
    total = uptime_sec + downtime_sec
    uptime_pct = (uptime_sec / total * 100) if total > 0 else 100.0
    
    # Check if currently down
    currently_down = False
    last_iv = db.query(models.EndpointInterval).filter(
        models.EndpointInterval.endpoint_id == endpoint_id
    ).order_by(models.EndpointInterval.start_time.desc()).first()
    if last_iv and last_iv.status == 'down':
        currently_down = True
        
    return {
        "uptime_pct": round(uptime_pct, 2),
        "downtime_seconds": downtime_sec,
        "outages": outages,
        "currently_down": currently_down,
        "current_down_duration": (datetime.utcnow() - last_iv.start_time).total_seconds() if currently_down else 0
    }

@app.get("/api/endpoints/{endpoint_id}/events")
def get_endpoint_events(endpoint_id: int, hours: float = 168.0, db: Session = Depends(get_db)):
    since = datetime.utcnow() - timedelta(hours=hours)
    intervals = db.query(models.EndpointInterval).filter(
        models.EndpointInterval.endpoint_id == endpoint_id,
        models.EndpointInterval.end_time >= since
    ).order_by(models.EndpointInterval.start_time.desc()).all()
    
    out = []
    for iv in intervals:
        start = max(iv.start_time, since)
        end = iv.end_time or datetime.utcnow()
        dur = (end - start).total_seconds()
        out.append({
            "id": iv.id,
            "status": iv.status,
            "from_time": start.isoformat(),
            "to_time": end.isoformat(),
            "duration_seconds": dur
        })
    return out

@app.get("/api/endpoints/{endpoint_id}/root_cause")
def get_root_cause(endpoint_id: int, from_time: str, to_time: str, db: Session = Depends(get_db)):
    start = datetime.fromisoformat(from_time)
    end = datetime.fromisoformat(to_time)
    
    results = db.query(models.MonitoringResult).filter(
        models.MonitoringResult.endpoint_id == endpoint_id,
        models.MonitoringResult.timestamp >= start,
        models.MonitoringResult.timestamp <= end
    ).all()
    
    if not results:
        return {"causes": [{"type": "Unknown", "confidence": "Low", "evidence": "No telemetry data found for this period."}]}
        
    avg_cpu = sum(r.server_cpu_percent or 0 for r in results) / len(results)
    avg_mem = sum(r.server_memory_percent or 0 for r in results) / len(results)
    max_latency = max(r.response_time_ms or 0 for r in results)
    error_count = sum(1 for r in results if not r.is_available)
    error_rate = (error_count / len(results)) * 100
    anomalies = sum(1 for r in results if r.is_anomaly)
    
    endpoint = db.query(models.Endpoint).filter(models.Endpoint.id == endpoint_id).first()
    timeout = endpoint.timeout_ms if endpoint else 5000
    
    causes = []
    
    if avg_cpu > 80:
        causes.append({"type": "CPU Saturation", "confidence": "High", "evidence": f"Average CPU was {avg_cpu:.1f}% during outage."})
    if max_latency > timeout:
        causes.append({"type": "Timeout / Upstream Unresponsive", "confidence": "High", "evidence": f"Max latency hit {max_latency}ms (Timeout: {timeout}ms)."})
    if avg_mem > 90:
        causes.append({"type": "Memory Pressure", "confidence": "Medium", "evidence": f"Average memory reached {avg_mem:.1f}%."})
    if error_rate > 50:
        causes.append({"type": "Service Error Surge", "confidence": "Medium", "evidence": f"Error rate spiked to {error_rate:.1f}%."})
    if anomalies > 0:
        causes.append({"type": "Anomalous Pattern Detected", "confidence": "Medium", "evidence": f"ML Engine flagged {anomalies} anomalies during outage."})
        
    if not causes:
        causes.append({"type": "Unknown Interruption", "confidence": "Low", "evidence": "Service was unavailable but metrics were normal."})
        
    return {"causes": causes}

@app.get("/api/endpoints/{endpoint_id}/test_logs")
def get_test_logs(endpoint_id: int, from_time: str, to_time: str, db: Session = Depends(get_db)):
    start = datetime.fromisoformat(from_time)
    end = datetime.fromisoformat(to_time)
    
    # Get all results for this interval
    results = db.query(models.MonitoringResult).filter(
        models.MonitoringResult.endpoint_id == endpoint_id,
        models.MonitoringResult.timestamp >= start,
        models.MonitoringResult.timestamp <= end
    ).order_by(models.MonitoringResult.timestamp.asc()).all()
    
    if not results:
        return []
        
    # Cap to first 5 and last 5
    if len(results) > 10:
        capped = results[:5] + results[-5:]
    else:
        capped = results
        
    out = []
    for r in capped:
        out.append({
            "timestamp": r.timestamp.isoformat(),
            "response_time_ms": r.response_time_ms,
            "is_available": r.is_available,
            "status_code": r.status_code,
            "server_cpu_percent": r.server_cpu_percent,
            "server_memory_percent": r.server_memory_percent,
            "error_message": r.error_message,
            "is_anomaly": r.is_anomaly
        })
    return out

@app.post("/api/ingest")
def ingest_request_logs(logs: list[schemas.RequestLogCreate], db: Session = Depends(get_db)):
    db_logs = []
    for log in logs:
        db_logs.append(models.RequestLog(
            endpoint=log.endpoint,
            method=log.method,
            status_code=log.status_code,
            duration_ms=log.duration_ms,
            timestamp=log.timestamp
        ))
    db.add_all(db_logs)
    db.commit()
    return {"status": "success", "inserted": len(db_logs)}

@app.get("/api/endpoints/{endpoint_id}/metrics")
def get_endpoint_metrics(endpoint_id: int, hours: int = 24, db: Session = Depends(get_db)):
    endpoint = db.query(models.Endpoint).filter(models.Endpoint.id == endpoint_id).first()
    if not endpoint:
        return []
        
    # Get MetricBuckets for this endpoint's URL
    start_time = datetime.utcnow() - timedelta(hours=hours)
    buckets = db.query(models.MetricBucket).filter(
        models.MetricBucket.endpoint.like(f"%{endpoint.url}%"),
        models.MetricBucket.bucket_minute >= start_time
    ).order_by(models.MetricBucket.bucket_minute.asc()).all()
    
    out = []
    for b in buckets:
        out.append({
            "timestamp": b.bucket_minute.isoformat(),
            "p50_latency_ms": b.p50_latency_ms,
            "p95_latency_ms": b.p95_latency_ms,
            "p99_latency_ms": b.p99_latency_ms,
            "rps": b.rps,
            "error_rate": b.error_rate,
            "is_anomaly": b.is_anomaly,
            "anomaly_label": b.anomaly_label
        })
    return out

@app.get("/api/endpoints/{endpoint_id}/slo")
def get_endpoint_slo(endpoint_id: int, db: Session = Depends(get_db)):
    endpoint = db.query(models.Endpoint).filter(models.Endpoint.id == endpoint_id).first()
    if not endpoint:
        return {"error": "not found"}
        
    slo = db.query(models.SLO).filter(models.SLO.endpoint.like(f"%{endpoint.url}%")).first()
    if not slo:
        return {"has_slo": False}
        
    # Calculate current burn rate
    from sqlalchemy import func
    now = datetime.utcnow()
    window_seconds = slo.window_hours * 3600
    window_start = now - timedelta(hours=slo.window_hours)
    
    stats = db.query(
        func.sum(models.MetricBucket.request_count).label('total_requests'),
        func.sum(models.MetricBucket.error_count).label('total_errors')
    ).filter(
        models.MetricBucket.endpoint == slo.endpoint,
        models.MetricBucket.bucket_minute >= window_start
    ).first()
    
    total_requests = stats.total_requests or 0
    actual_errors = stats.total_errors or 0
    
    first_bucket = db.query(func.min(models.MetricBucket.bucket_minute)).filter(
        models.MetricBucket.endpoint == slo.endpoint
    ).scalar()
    
    burn_rate = 0.0
    if first_bucket and total_requests > 0:
        time_running = (now - first_bucket).total_seconds()
        elapsed_seconds = min(time_running, window_seconds)
        elapsed_fraction = elapsed_seconds / window_seconds
        
        allowed_errors = total_requests * (1 - slo.target)
        expected_errors = allowed_errors * elapsed_fraction
        if expected_errors > 0:
            burn_rate = actual_errors / expected_errors
            
    return {
        "has_slo": True,
        "target": slo.target,
        "window_hours": slo.window_hours,
        "total_requests": total_requests,
        "actual_errors": actual_errors,
        "burn_rate": burn_rate
    }



# ---------- Alerts ----------

@app.get("/api/alerts", response_model=List[schemas.AlertOut])
def get_alerts(active_only: bool = False, db: Session = Depends(get_db)):
    q = db.query(models.Alert)
    if active_only:
        q = q.filter(models.Alert.resolved_at.is_(None))
    return q.order_by(models.Alert.triggered_at.desc()).limit(200).all()


# ---------- Dashboard (static frontend) ----------

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/endpoint/{endpoint_id}")
async def endpoint_view(endpoint_id: int):
    return FileResponse("static/endpoint.html")


@app.get("/api/reports/sla", response_model=schemas.SLAReportOut)
def get_sla_report(
    month: str = None, # e.g. "2026-09"
    db: Session = Depends(get_db)
):
    from sqlalchemy import func
    from datetime import datetime, timedelta
    from fastapi import HTTPException
    
    now = datetime.utcnow()
    
    if month:
        try:
            start_date = datetime.strptime(month, "%Y-%m")
            # fast way to get next month
            end_date = (start_date.replace(day=28) + timedelta(days=4)).replace(day=1)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid month format, use YYYY-MM")
    else:
        # Default to current month
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = now
        
    total_minutes = (end_date - start_date).total_seconds() / 60.0
    if total_minutes <= 0:
        total_minutes = 1 # avoid div by zero
        
    num_endpoints = db.query(models.Endpoint).count()
    if num_endpoints == 0:
        return schemas.SLAReportOut(
            total_endpoints=0, total_incidents=0,
            global_mttr_minutes=0.0, global_mtbf_hours=0.0,
            availability_pct=100.0, top_failing_endpoints=[]
        )
        
    incidents = db.query(models.Incident).filter(
        models.Incident.start_time >= start_date,
        models.Incident.start_time < end_date,
        models.Incident.root_cause == "unavailable"
    ).all()
    
    total_incidents = len(incidents)
    total_downtime_minutes = 0.0
    resolved_durations = []
    
    endpoint_fail_counts = {}
    
    for inc in incidents:
        ep_id = inc.endpoint_id
        endpoint_fail_counts[ep_id] = endpoint_fail_counts.get(ep_id, 0) + 1
        
        if inc.status == "resolved" and inc.duration_minutes is not None:
            dur = inc.duration_minutes
            total_downtime_minutes += dur
            resolved_durations.append(dur)
        else:
            # still open
            dur = (now - inc.start_time).total_seconds() / 60.0
            total_downtime_minutes += dur

    global_mttr = sum(resolved_durations) / len(resolved_durations) if resolved_durations else 0.0
    
    max_possible_uptime_minutes = total_minutes * num_endpoints
    total_uptime_minutes = max_possible_uptime_minutes - total_downtime_minutes
    if total_uptime_minutes < 0:
        total_uptime_minutes = 0
        
    global_mtbf_hours = (total_uptime_minutes / total_incidents) / 60.0 if total_incidents > 0 else (total_uptime_minutes / 60.0)
    
    availability_pct = (total_uptime_minutes / max_possible_uptime_minutes) * 100.0
    
    top_failing = []
    if endpoint_fail_counts:
        sorted_eps = sorted(endpoint_fail_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        for ep_id, count in sorted_eps:
            ep = db.query(models.Endpoint).filter(models.Endpoint.id == ep_id).first()
            if ep:
                top_failing.append({"endpoint_id": ep_id, "name": ep.name, "incident_count": count})

    return schemas.SLAReportOut(
        total_endpoints=num_endpoints,
        total_incidents=total_incidents,
        global_mttr_minutes=global_mttr,
        global_mtbf_hours=global_mtbf_hours,
        availability_pct=availability_pct,
        top_failing_endpoints=top_failing
    )

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

from app.rca import analyze_incident_root_cause

@app.get("/api/incidents/{incident_id}/rca", response_model=schemas.IncidentRCAOut)
def get_incident_rca(incident_id: int, db: Session = Depends(get_db)):
    result = analyze_incident_root_cause(db, incident_id)
    if not result:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Incident not found")
    return result
@app.get("/api/endpoints/{endpoint_id}/incidents", response_model=list[schemas.IncidentOut])
def get_endpoint_incidents(endpoint_id: int, limit: int = 50, db: Session = Depends(get_db)):
    from datetime import datetime
    incidents = (
        db.query(models.Incident)
        .filter(models.Incident.endpoint_id == endpoint_id)
        .order_by(models.Incident.start_time.desc())
        .limit(limit)
        .all()
    )
    
    for inc in incidents:
        if inc.duration_minutes is None:
            end = inc.resolution_time or datetime.utcnow()
            inc.duration_minutes = (end - inc.start_time).total_seconds() / 60.0
            
    return incidents
