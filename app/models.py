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

    results = relationship("MonitoringResult", back_populates="endpoint", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="endpoint", cascade="all, delete-orphan")


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
