import threading
import queue
import logging
from datetime import datetime
from .database import SessionLocal
from .models import Endpoint, MonitoringResult
from .alerts import evaluate_alerts

logger = logging.getLogger("apm.worker")

# The in-memory message broker (simulating Kafka/Redis for the prototype)
telemetry_queue = queue.Queue()

def process_telemetry():
    """Background worker that continuously consumes telemetry from the queue
    and processes it (saving to DB, triggering alerts, running ML inference)."""
    logger.info("Telemetry worker started. Listening for messages...")
    while True:
        try:
            # Block until an item is available
            message = telemetry_queue.get()
            if message is None:
                break  # Poison pill to stop the thread
            
            endpoint_id = message["endpoint_id"]
            result_data = message["result_data"]
            
            db = SessionLocal()
            try:
                endpoint = db.query(Endpoint).filter(Endpoint.id == endpoint_id).first()
                if not endpoint or not endpoint.is_active:
                    continue

                # Run ML anomaly detection
                from .ml_engine import detect_anomaly
                is_anomaly, anomaly_score = detect_anomaly(endpoint.id, result_data.get("response_time_ms"))

                # 1. Save telemetry to time-series DB (simulated by SQLite here)
                result = MonitoringResult(
                    endpoint_id=endpoint.id,
                    timestamp=datetime.utcnow(),
                    is_anomaly=is_anomaly,
                    anomaly_score=anomaly_score,
                    **result_data,
                )
                db.add(result)
                db.commit()
                db.refresh(result)

                logger.info(
                    "Processed telemetry for %s -> available=%s status=%s time=%sms",
                    endpoint.name, result.is_available, result.status_code, result.response_time_ms
                )

                # 2. Evaluate Alerts (which will later include ML anomaly flags)
                evaluate_alerts(db, endpoint, result)
            finally:
                db.close()
            
            telemetry_queue.task_done()
        except Exception as e:
            logger.error(f"Error processing telemetry: {e}")

# Start the worker thread
worker_thread = threading.Thread(target=process_telemetry, daemon=True)

def start_worker():
    if not worker_thread.is_alive():
        worker_thread.start()
