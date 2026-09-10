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

    icon = "🔴" if alert.severity == "critical" else "🟠"
    send_teams_alert(f"{icon} **{endpoint.name}** — {alert.message}")


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


def _raise_alert_if_new(db: Session, endpoint: Endpoint, alert_type: str, severity: str, message: str):
    """Only creates + notifies a new alert if there isn't already an open
    (unresolved) alert of the same type for this endpoint — prevents spamming
    a notification on every single poll cycle."""
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
        return  # already firing, don't re-notify

    alert = Alert(
        endpoint_id=endpoint.id,
        alert_type=alert_type,
        severity=severity,
        message=message,
        triggered_at=datetime.utcnow(),
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    dispatch_notification(endpoint, alert)
    alert.notified = True
    db.commit()


def _resolve_open_alert(db: Session, endpoint: Endpoint, alert_type: str):
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
        open_alert.resolved_at = datetime.utcnow()
        db.commit()
        send_teams_alert(f"✅ **{endpoint.name}** recovered ({alert_type} resolved).")
