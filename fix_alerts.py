import os

with open('app/alerts.py', 'r') as f:
    content = f.read()

# Replace _raise_alert_if_new and _resolve_open_alert first
new_helpers = '''
def _raise_alert_if_new(db: Session, endpoint: Endpoint, alert_type: str, severity: str, message: str, start_time=None):
    from .models import Incident
    open_alert = (
        db.query(Alert)
        .filter(
            Alert.endpoint_id == endpoint.id,
            Alert.alert_type == alert_type,
            Alert.resolved_at.is_(None),
        )
        .first()
    )
    if open_alert:
        return

    now = datetime.utcnow()
    alert = Alert(
        endpoint_id=endpoint.id,
        alert_type=alert_type,
        severity=severity,
        message=message,
        triggered_at=now,
    )
    db.add(alert)
    
    # Also create an Incident
    open_incident = db.query(Incident).filter(
        Incident.endpoint_id == endpoint.id,
        Incident.status == "open",
        Incident.root_cause == alert_type
    ).first()
    
    if not open_incident:
        incident = Incident(
            endpoint_id=endpoint.id,
            status="open",
            severity=severity,
            start_time=start_time or now,
            assigned_team=getattr(endpoint, "team_name", "Unassigned"),
            root_cause=alert_type,
            error_message=message
        )
        db.add(incident)

    db.commit()
    db.refresh(alert)

    dispatch_notification(endpoint, alert)
    alert.notified = True
    db.commit()


def _resolve_open_alert(db: Session, endpoint: Endpoint, alert_type: str):
    from .models import Incident
    now = datetime.utcnow()
    
    open_alert = (
        db.query(Alert)
        .filter(
            Alert.endpoint_id == endpoint.id,
            Alert.alert_type == alert_type,
            Alert.resolved_at.is_(None),
        )
        .first()
    )
    if open_alert:
        open_alert.resolved_at = now
        
    open_incident = db.query(Incident).filter(
        Incident.endpoint_id == endpoint.id,
        Incident.status == "open",
        Incident.root_cause == alert_type
    ).first()
    
    if open_incident:
        open_incident.status = "resolved"
        open_incident.resolution_time = now
        open_incident.duration_minutes = (now - open_incident.start_time).total_seconds() / 60.0

    if open_alert or open_incident:
        db.commit()
        send_teams_alert(f"✅ **{endpoint.name}** recovered ({alert_type} resolved).")
'''

# Find where _raise_alert_if_new starts and replace till the end of _resolve_open_alert
import re
pattern = re.compile(r'def _raise_alert_if_new.*?def evaluate_slo_alerts', re.DOTALL)
content = pattern.sub(new_helpers + '\n\ndef evaluate_slo_alerts', content)

# Now update the evaluate_alerts Rule 1 logic
rule1_old = '''    if not result.is_available:
        recent = (
            db.query(MonitoringResult)
            .filter(MonitoringResult.endpoint_id == endpoint.id)
            .order_by(desc(MonitoringResult.timestamp))
            .limit(endpoint.consecutive_failures_for_alert)
            .all()
        )
        if len(recent) >= endpoint.consecutive_failures_for_alert and all(
            not r.is_available for r in recent
        ):
            _raise_alert_if_new(
                db, endpoint,
                alert_type="unavailable",
                severity="critical",
                message=(
                    f"{endpoint.name} has failed {len(recent)} consecutive checks "
                    f"(last error: {result.error_message or f'HTTP {result.status_code}'})."
                ),
            )
    else:
        # Endpoint responded fine -> resolve any open "unavailable" alert
        _resolve_open_alert(db, endpoint, alert_type="unavailable")'''

rule1_new = '''    if not result.is_available:
        recent = (
            db.query(MonitoringResult)
            .filter(MonitoringResult.endpoint_id == endpoint.id)
            .order_by(desc(MonitoringResult.timestamp))
            .limit(endpoint.consecutive_failures_for_alert)
            .all()
        )
        if len(recent) >= endpoint.consecutive_failures_for_alert and all(
            not r.is_available for r in recent
        ):
            # Pass the start_time of the FIRST failure (the oldest one in this window)
            first_failure_time = recent[-1].timestamp
            _raise_alert_if_new(
                db, endpoint,
                alert_type="unavailable",
                severity="critical",
                message=(
                    f"{endpoint.name} has failed {len(recent)} consecutive checks "
                    f"(last error: {result.error_message or f'HTTP {result.status_code}'})."
                ),
                start_time=first_failure_time
            )
    else:
        # Endpoint responded fine -> Check if we can resolve "unavailable"
        from .models import Incident
        open_incident = db.query(Incident).filter(
            Incident.endpoint_id == endpoint.id, 
            Incident.status == "open", 
            Incident.root_cause == "unavailable"
        ).first()
        
        if open_incident:
            # Need 2 consecutive successes to recover
            recent_success = (
                db.query(MonitoringResult)
                .filter(MonitoringResult.endpoint_id == endpoint.id)
                .order_by(desc(MonitoringResult.timestamp))
                .limit(2)
                .all()
            )
            if len(recent_success) >= 2 and all(r.is_available for r in recent_success):
                _resolve_open_alert(db, endpoint, alert_type="unavailable")
        else:
            # If no open incident, just resolve the alert if it exists
            _resolve_open_alert(db, endpoint, alert_type="unavailable")'''

content = content.replace(rule1_old, rule1_new)

with open('app/alerts.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated alerts.py")
