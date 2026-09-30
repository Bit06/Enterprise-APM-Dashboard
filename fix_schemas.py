import os

with open('app/schemas.py', 'r') as f:
    content = f.read()

# Add team_name to EndpointCreate
content = content.replace('consecutive_failures_for_alert: int = 2', 'consecutive_failures_for_alert: int = 2\n    team_name: Optional[str] = None')

# Add Incident schema and SLA schemas
schemas = '''
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
'''
content = content.replace('class EndpointStatus', schemas + '\nclass EndpointStatus')

with open('app/schemas.py', 'w') as f:
    f.write(content)
print("Updated schemas.py")
