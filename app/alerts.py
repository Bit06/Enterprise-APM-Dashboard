"""
Alert & Notification Service.

Evaluates each new monitoring result against thresholds (availability,
consecutive failures, response time) and raises/resolves alerts.
Notifications are dispatched via email (SMTP) and/or Microsoft Teams
(incoming webhook).
"""
import os
import logging
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

import requests
from sqlalchemy.orm import Session
from sqlalchemy import desc

from .models import Endpoint, MonitoringResult, Alert

logger = logging.getLogger("apm.alerts")

# --- Notification channel config (set these via environment variables) ---
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
ALERT_EMAIL_FROM = os.getenv("ALERT_EMAIL_FROM", SMTP_USER or "apm@example.com")
ALERT_EMAIL_TO = os.getenv("ALERT_EMAIL_TO")  # comma-separated list

TEAMS_WEBHOOK_URL = os.getenv("TEAMS_WEBHOOK_URL")


def send_email_alert(subject: str, body: str):
    if not (SMTP_HOST and ALERT_EMAIL_TO):
        logger.info("[email disabled - no SMTP_HOST/ALERT_EMAIL_TO set] %s: %s", subject, body)
        return
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = ALERT_EMAIL_FROM
    msg["To"] = ALERT_EMAIL_TO
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            if SMTP_USER and SMTP_PASSWORD:
                server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(ALERT_EMAIL_FROM, ALERT_EMAIL_TO.split(","), msg.as_string())
        logger.info("Email alert sent: %s", subject)
    except Exception as e:
        logger.error("Failed to send email alert: %s", e)


def send_teams_alert(text: str):
    if not TEAMS_WEBHOOK_URL:
        logger.info("[teams disabled - no TEAMS_WEBHOOK_URL set] %s", text)
        return
    try:
        requests.post(TEAMS_WEBHOOK_URL, json={"text": text}, timeout=10)
        logger.info("Teams alert sent.")
    except Exception as e:
        logger.error("Failed to send Teams alert: %s", e)


def dispatch_notification(endpoint: Endpoint, alert: Alert):
    subject = f"[APM] {alert.severity.upper()} - {endpoint.name}"
    body = (
        f"Endpoint: {endpoint.name} ({endpoint.url})\n"
        f"Environment: {endpoint.environment}\n"
        f"Alert type: {alert.alert_type}\n"
        f"Severity: {alert.severity}\n"
        f"Message: {alert.message}\n"
        f"Triggered at: {alert.triggered_at.isoformat()} UTC"
    )
    send_email_alert(subject, body)

    icon = "ðŸ”´" if alert.severity == "critical" else "ðŸŸ "
    send_teams_alert(f"{icon} **{endpoint.name}** â€” {alert.message}")


def evaluate_alerts(db: Session, endpoint: Endpoint, result: MonitoringResult):
    """Core alerting logic, called after every probe."""

    # --- Rule 1: consecutive failures -> "unavailable" alert ---
    if not result.is_available:
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
            _resolve_open_alert(db, endpoint, alert_type="unavailable")

        # --- Rule 2: HTTP error codes (e.g. 500s) even if "available" flag differs ---
        if result.status_code and result.status_code >= 500:
            _raise_alert_if_new(
                db, endpoint,
                alert_type="http_error",
                severity="critical",
                message=f"{endpoint.name} returned HTTP {result.status_code}.",
            )
        else:
            _resolve_open_alert(db, endpoint, alert_type="http_error")

        # --- Rule 3: response time thresholds ---
        rt = result.response_time_ms or 0
        if rt >= endpoint.response_time_critical_ms:
            _raise_alert_if_new(
                db, endpoint,
                alert_type="slow_response",
                severity="critical",
                message=f"{endpoint.name} response time {rt:.0f}ms exceeds critical threshold "
                        f"({endpoint.response_time_critical_ms}ms).",
            )
        elif rt >= endpoint.response_time_warn_ms:
            _raise_alert_if_new(
                db, endpoint,
                alert_type="slow_response",
                severity="warning",
                message=f"{endpoint.name} response time {rt:.0f}ms exceeds warning threshold "
                        f"({endpoint.response_time_warn_ms}ms).",
            )
        else:
            _resolve_open_alert(db, endpoint, alert_type="slow_response")

        # --- Rule 4: ML Anomaly Detection ---
        if getattr(result, "is_anomaly", False):
            _raise_alert_if_new(
                db, endpoint,
                alert_type="ml_anomaly",
                severity="warning",
                message=f"ML Engine detected anomalous behavior for {endpoint.name} "
                        f"(Anomaly Score: {result.anomaly_score:.2f}).",
            )
        else:
            _resolve_open_alert(db, endpoint, alert_type="ml_anomaly")



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


def evaluate_slo_alerts(db: Session):
    """Calculates SLO error budgets and alerts on > 2x burn rate."""
    from .models import SLO, MetricBucket, Endpoint
    from sqlalchemy import func
    from datetime import timedelta
    
    slos = db.query(SLO).all()
    for slo in slos:
        now = datetime.utcnow()
        window_seconds = slo.window_hours * 3600
        window_start = now - timedelta(hours=slo.window_hours)
        
        # Get total requests and total errors in window
        stats = db.query(
            func.sum(MetricBucket.request_count).label('total_requests'),
            func.sum(MetricBucket.error_count).label('total_errors')
        ).filter(
            MetricBucket.endpoint == slo.endpoint,
            MetricBucket.bucket_minute >= window_start
        ).first()
        
        total_requests = stats.total_requests or 0
        actual_errors = stats.total_errors or 0
        
        if total_requests == 0:
            continue
            
        allowed_errors = total_requests * (1 - slo.target)
        
        first_bucket = db.query(func.min(MetricBucket.bucket_minute)).filter(
            MetricBucket.endpoint == slo.endpoint
        ).scalar()
        
        if not first_bucket:
            continue
            
        time_running = (now - first_bucket).total_seconds()
        elapsed_seconds = min(time_running, window_seconds)
        
        elapsed_fraction = elapsed_seconds / window_seconds
        expected_errors_so_far = allowed_errors * elapsed_fraction
        
        if expected_errors_so_far > 0:
            burn_rate = actual_errors / expected_errors_so_far
        else:
            burn_rate = 0
            
        endpoint_obj = db.query(Endpoint).filter(Endpoint.url.endswith(slo.endpoint)).first()
        if not endpoint_obj:
            # If no formal endpoint maps to this path, fallback to ID 1 or skip
            endpoint_obj = db.query(Endpoint).first()
            if not endpoint_obj:
                continue
            
        if burn_rate > 2.0:
            _raise_alert_if_new(
                db, endpoint_obj,
                alert_type="slo_burn_rate",
                severity="critical",
                message=f"SLO Burn Rate is {burn_rate:.1f}x for {slo.endpoint} (Target: {slo.target*100}%)."
            )
        else:
            _resolve_open_alert(db, endpoint_obj, alert_type="slo_burn_rate")
