from datetime import datetime, timedelta
from typing import List

from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
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

        out.append(schemas.EndpointStatus(
            endpoint_id=ep.id,
            name=ep.name,
            environment=ep.environment,
            url=ep.url,
            is_available=latest.is_available if latest else False,
            status_code=latest.status_code if latest else None,
            response_time_ms=latest.response_time_ms if latest else None,
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


# ---------- Alerts ----------

@app.get("/api/alerts", response_model=List[schemas.AlertOut])
def get_alerts(active_only: bool = False, db: Session = Depends(get_db)):
    q = db.query(models.Alert)
    if active_only:
        q = q.filter(models.Alert.resolved_at.is_(None))
    return q.order_by(models.Alert.triggered_at.desc()).limit(200).all()


# ---------- Dashboard (static frontend) ----------

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def dashboard():
    return FileResponse("static/index.html")
