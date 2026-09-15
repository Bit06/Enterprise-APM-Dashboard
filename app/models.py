from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
)
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class Endpoint(Base):
    """A registered API or application endpoint to monitor."""
    __tablename__ = "endpoints"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    url = Column(String(500), nullable=False)
    environment = Column(String(100), default="production")  # e.g. IIS, Ubuntu, staging
    check_interval_seconds = Column(Integer, default=60)
    timeout_seconds = Column(Integer, default=10)
    response_time_warn_ms = Column(Integer, default=1000)   # threshold: "degraded"
    response_time_critical_ms = Column(Integer, default=3000)  # threshold: "critical"
    consecutive_failures_for_alert = Column(Integer, default=2)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    team_name = Column(String(100), nullable=True)

    results = relationship("MonitoringResult", back_populates="endpoint", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="endpoint", cascade="all, delete-orphan")
    intervals = relationship("EndpointInterval", back_populates="endpoint", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="endpoint", cascade="all, delete-orphan")


class MonitoringResult(Base):
    """A single probe result for an endpoint."""
    __tablename__ = "monitoring_results"

    id = Column(Integer, primary_key=True, index=True)
    endpoint_id = Column(Integer, ForeignKey("endpoints.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    status_code = Column(Integer, nullable=True)
    response_time_ms = Column(Float, nullable=True)
    is_available = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    
    server_cpu_percent = Column(Float, nullable=True)
    server_memory_percent = Column(Float, nullable=True)
    
    # ML Fields
    is_anomaly = Column(Boolean, default=False)
    anomaly_score = Column(Float, nullable=True)

    endpoint = relationship("Endpoint", back_populates="results")


class Alert(Base):
    """A triggered alert / incident for an endpoint."""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    endpoint_id = Column(Integer, ForeignKey("endpoints.id"), nullable=False, index=True)
    alert_type = Column(String(50))       # e.g. "unavailable", "slow_response", "http_error"
    severity = Column(String(20))         # e.g. "warning", "critical"
    message = Column(Text)
    triggered_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    notified = Column(Boolean, default=False)

    endpoint = relationship("Endpoint", back_populates="alerts")

class Incident(Base):
    """A tracked lifecycle of an outage or severe degradation."""
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    endpoint_id = Column(Integer, ForeignKey("endpoints.id"), nullable=False, index=True)
    status = Column(String(20), default="open") # open, resolved
    severity = Column(String(20), default="critical") # e.g. critical, warning
    start_time = Column(DateTime, default=datetime.utcnow, index=True)
    resolution_time = Column(DateTime, nullable=True)
    duration_minutes = Column(Float, nullable=True)
    assigned_team = Column(String(100), nullable=True)
    root_cause = Column(String(500), nullable=True)
    error_message = Column(Text, nullable=True)

    endpoint = relationship("Endpoint", back_populates="incidents")


class EndpointInterval(Base):
    """Tracks continuous UP or DOWN intervals for an endpoint."""
    __tablename__ = "endpoint_intervals"

    id = Column(Integer, primary_key=True, index=True)
    endpoint_id = Column(Integer, ForeignKey("endpoints.id"), nullable=False, index=True)
    status = Column(String(20), nullable=False) # 'up' or 'down'
    start_time = Column(DateTime, default=datetime.utcnow, index=True)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, default=0.0)

    endpoint = relationship("Endpoint", back_populates="intervals")


class RequestLog(Base):
    """Raw incoming telemetry from the dummy app."""
    __tablename__ = "request_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    endpoint = Column(String(500), index=True)
    method = Column(String(20), index=True)
    status_code = Column(Integer)
    duration_ms = Column(Float)
    timestamp = Column(Float, index=True)


class MetricBucket(Base):
    """Aggregated APM metrics per minute."""
    __tablename__ = "metric_buckets"
    
    id = Column(Integer, primary_key=True, index=True)
    endpoint = Column(String(500), index=True)
    method = Column(String(20), index=True)
    bucket_minute = Column(DateTime, index=True)
    
    request_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    error_rate = Column(Float, default=0.0)
    rps = Column(Float, default=0.0)
    
    p50_latency_ms = Column(Float, default=0.0)
    p95_latency_ms = Column(Float, default=0.0)
    p99_latency_ms = Column(Float, default=0.0)
    
    # Optional fields for ML anomaly labels
    is_anomaly = Column(Boolean, default=False)
    anomaly_label = Column(String(100), nullable=True)


class SLO(Base):
    """Service Level Objectives for error budgets."""
    __tablename__ = "slos"
    
    id = Column(Integer, primary_key=True, index=True)
    endpoint = Column(String(500), index=True)
    target = Column(Float, default=0.99) # e.g., 0.999 for 99.9%
    window_hours = Column(Integer, default=30)
