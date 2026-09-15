from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class EndpointCreate(BaseModel):
    name: str
    url: str
    environment: str = "production"
    check_interval_seconds: int = 60
    timeout_seconds: int = 10
    response_time_warn_ms: int = 1000
    response_time_critical_ms: int = 3000
    consecutive_failures_for_alert: int = 2
    team_name: Optional[str] = None


class EndpointOut(EndpointCreate):
    id: int
    is_active: bool

    class Config:
        from_attributes = True


class MonitoringResultCreate(BaseModel):
    timestamp: datetime
    status_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    is_available: bool
    error_message: Optional[str] = None
    server_cpu_percent: Optional[float] = None
    server_memory_percent: Optional[float] = None


class MonitoringResultOut(MonitoringResultCreate):
    id: int
    endpoint_id: int
    is_anomaly: bool = False
    anomaly_score: Optional[float] = None

    class Config:
        from_attributes = True


class ForecastOut(BaseModel):
    endpoint_id: int
    forecasted_response_times: list[float]


class AlertOut(BaseModel):
    id: int
    endpoint_id: int
    alert_type: str
    severity: str
    message: str
    triggered_at: datetime
    resolved_at: Optional[datetime]

    class Config:
        from_attributes = True



class IncidentOut(BaseModel):
    id: int
    endpoint_id: int
    status: str
    severity: str
    start_time: datetime
    resolution_time: Optional[datetime]
    duration_minutes: Optional[float]
    assigned_team: Optional[str]
    root_cause: Optional[str]
    error_message: Optional[str]

    class Config:
        from_attributes = True

class SLAReportOut(BaseModel):
    total_endpoints: int
    total_incidents: int
    global_mttr_minutes: float
    global_mtbf_hours: float
    availability_pct: float
    top_failing_endpoints: list[dict]

class EndpointStatus(BaseModel):
    """Live status summary shown on the dashboard grid."""
    endpoint_id: int
    name: str
    environment: str
    url: str
    is_available: bool
    status_code: Optional[int]
    response_time_ms: Optional[float]
    p99_latency_ms: Optional[float]
    rps: Optional[float]
    error_rate: Optional[float]
    slo_burn_rate: Optional[float]
    last_checked: Optional[datetime]
    health: str  # "up" | "degraded" | "down" | "unknown"
    availability_pct_24h: float

class RequestLogCreate(BaseModel):
    endpoint: str
    method: str
    status_code: int
    duration_ms: float
    timestamp: float

class RCARuleOut(BaseModel):
    rule: str
    confidence: str
    evidence: str
    threshold: float

class TelemetrySnapshotOut(BaseModel):
    id: int
    timestamp: datetime
    status_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    is_available: bool
    error_message: Optional[str] = None
    server_cpu_percent: Optional[float] = None
    server_memory_percent: Optional[float] = None

class IncidentRCAOut(BaseModel):
    incident_id: int
    rca_analysis: list[RCARuleOut]
    telemetry_snapshot: list[TelemetrySnapshotOut]
