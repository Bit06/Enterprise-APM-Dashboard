with open('app/schemas.py', 'a', encoding='utf-8') as f:
    f.write('''
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
''')
print('Appended schemas')
