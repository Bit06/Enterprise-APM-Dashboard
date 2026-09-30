import os

with open('app/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_route = '''
@app.get("/api/reports/sla", response_model=schemas.SLAReportOut)
def get_sla_report(
    month: Optional[str] = None, # e.g. "2026-09"
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
'''

# append right before @app.get("/")
import re
pattern = re.compile(r'(@app\.get\("/"\))', re.MULTILINE)
content = pattern.sub(new_route + r'\n\1', content)

with open('app/main.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated main.py")
