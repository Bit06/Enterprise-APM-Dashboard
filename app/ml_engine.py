import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler
from statsmodels.tsa.arima.model import ARIMA
import warnings

from .database import SessionLocal
from .models import Endpoint, MonitoringResult, MetricBucket

logger = logging.getLogger("apm.ml_engine")
warnings.filterwarnings("ignore")

# Features monitored across endpoints
FEATURE_NAMES = [
    "rps",
    "p95_latency_ms",
    "p99_latency_ms",
    "error_rate",
    "server_cpu_percent",
    "server_memory_percent"
]

# Model registry
# Keys: endpoint_id or endpoint_url
# Value: dict containing model, scaler, threshold, baseline stats, state
anomaly_registry = {}

MIN_TRAINING_SAMPLES = 25

def train_anomaly_models():
    """
    Fetches recent historical telemetry and trains a Multivariate Isolation Forest
    with RobustScaler for each active endpoint. If insufficient data exists,
    registers the endpoint in 'cold_start' mode using statistical baselines.
    """
    logger.info("Training multivariate ML anomaly detection models...")
    db = SessionLocal()
    try:
        endpoints = db.query(Endpoint).filter(Endpoint.is_active == True).all()
        since = datetime.utcnow() - timedelta(days=7)

        for ep in endpoints:
            ep_keys = [str(ep.id), ep.url, ep.name]

            # Fetch aggregated bucket metrics
            buckets = db.query(MetricBucket).filter(
                MetricBucket.endpoint.like(f"%{ep.url}%"),
                MetricBucket.bucket_minute >= since
            ).order_by(MetricBucket.bucket_minute.asc()).all()

            # Also fetch probe monitoring results for CPU/RAM correlation
            probes = db.query(MonitoringResult).filter(
                MonitoringResult.endpoint_id == ep.id,
                MonitoringResult.timestamp >= since
            ).order_by(MonitoringResult.timestamp.asc()).all()

            # Build multivariate feature dataset
            records = []
            if buckets and len(buckets) >= MIN_TRAINING_SAMPLES:
                for b in buckets:
                    # Match closest probe for CPU/RAM
                    cpu = 25.0
                    mem = 60.0
                    if probes:
                        closest = min(probes, key=lambda p: abs((p.timestamp - b.bucket_minute).total_seconds()))
                        if closest.server_cpu_percent is not None:
                            cpu = closest.server_cpu_percent
                        if closest.server_memory_percent is not None:
                            mem = closest.server_memory_percent

                    records.append({
                        "rps": float(b.rps or 0.0),
                        "p95_latency_ms": float(b.p95_latency_ms or 0.0),
                        "p99_latency_ms": float(b.p99_latency_ms or 0.0),
                        "error_rate": float(b.error_rate or 0.0),
                        "server_cpu_percent": float(cpu),
                        "server_memory_percent": float(mem)
                    })
            elif probes and len(probes) >= MIN_TRAINING_SAMPLES:
                for p in probes:
                    records.append({
                        "rps": 1.0,
                        "p95_latency_ms": float(p.response_time_ms or 0.0),
                        "p99_latency_ms": float(p.response_time_ms or 0.0),
                        "error_rate": 100.0 if (not p.is_available or (p.status_code and p.status_code >= 500)) else 0.0,
                        "server_cpu_percent": float(p.server_cpu_percent or 25.0),
                        "server_memory_percent": float(p.server_memory_percent or 60.0)
                    })

            # Check if sufficient data exists for model training
            if len(records) < MIN_TRAINING_SAMPLES:
                logger.info(
                    "Endpoint %s has only %d samples (< %d required). Operating in cold_start mode.",
                    ep.name, len(records), MIN_TRAINING_SAMPLES
                )
                cold_start_entry = {
                    "state": "cold_start",
                    "model": None,
                    "scaler": None,
                    "threshold": None,
                    "version": "baseline-fallback-v1.0",
                    "sample_count": len(records),
                    "warn_latency": ep.response_time_warn_ms,
                    "critical_latency": ep.response_time_critical_ms,
                    "medians": {},
                    "iqrs": {}
                }
                for k in ep_keys:
                    anomaly_registry[k] = cold_start_entry
                continue

            df = pd.DataFrame(records)[FEATURE_NAMES]

            # Fit RobustScaler only on training observations to avoid leakage
            scaler = RobustScaler()
            scaled_features = scaler.fit_transform(df)

            # Fit Isolation Forest (contamination=0.05)
            model = IsolationForest(
                n_estimators=100,
                contamination=0.05,
                random_state=42,
                n_jobs=-1
            )
            model.fit(scaled_features)

            # Determine empirical anomaly score threshold from training data
            scores = model.score_samples(scaled_features)
            score_threshold = float(np.percentile(scores, 1.0))  # 1st percentile of score (lower = more anomalous)

            # Store baseline statistics for feature deviation attribution
            medians = df.median().to_dict()
            iqrs = (df.quantile(0.75) - df.quantile(0.25)).replace(0, 1.0).to_dict()

            entry = {
                "state": "model_ready",
                "model": model,
                "scaler": scaler,
                "threshold": score_threshold,
                "version": "iforest-multivariate-v2.0",
                "sample_count": len(df),
                "medians": medians,
                "iqrs": iqrs,
                "warn_latency": ep.response_time_warn_ms,
                "critical_latency": ep.response_time_critical_ms
            }

            for k in ep_keys:
                anomaly_registry[k] = entry

            logger.info(
                "Successfully trained Multivariate Isolation Forest for %s on %d samples (threshold: %.4f).",
                ep.name, len(df), score_threshold
            )

    except Exception as e:
        logger.error("Error during ML model training: %s", e, exc_info=True)
    finally:
        db.close()

def detect_anomaly(endpoint_identifier, telemetry_input) -> tuple[bool, float, str, dict]:
    """
    Evaluates telemetry against either the trained Multivariate Isolation Forest
    or the statistical cold-start baseline fallback.

    Args:
        endpoint_identifier: Endpoint ID (int) or URL/name (str)
        telemetry_input: float (latency ms) or dict of features

    Returns:
        (is_anomaly: bool, anomaly_score: float, label: str, metadata: dict)
    """
    key = str(endpoint_identifier)
    reg = anomaly_registry.get(key)

    # Normalize input features into a dict
    features = {}
    if isinstance(telemetry_input, (int, float)):
        features = {
            "rps": 1.0,
            "p95_latency_ms": float(telemetry_input),
            "p99_latency_ms": float(telemetry_input),
            "error_rate": 0.0,
            "server_cpu_percent": 25.0,
            "server_memory_percent": 60.0
        }
    elif isinstance(telemetry_input, dict):
        features = {
            "rps": float(telemetry_input.get("rps", 1.0)),
            "p95_latency_ms": float(telemetry_input.get("p95_latency_ms", telemetry_input.get("response_time_ms", 0.0))),
            "p99_latency_ms": float(telemetry_input.get("p99_latency_ms", telemetry_input.get("response_time_ms", 0.0))),
            "error_rate": float(telemetry_input.get("error_rate", 0.0)),
            "server_cpu_percent": float(telemetry_input.get("server_cpu_percent", 25.0)),
            "server_memory_percent": float(telemetry_input.get("server_memory_percent", 60.0))
        }
    else:
        return False, 0.0, None, {"state": "unrecognized_input"}

    # --- Cold Start / Fallback Path ---
    if not reg or reg.get("state") != "model_ready":
        warn_lat = reg.get("warn_latency", 1000) if reg else 1000
        crit_lat = reg.get("critical_latency", 3000) if reg else 3000

        is_anom = False
        reason = None
        lat = features.get("p99_latency_ms", 0.0)

        if lat >= crit_lat:
            is_anom = True
            reason = "critical_latency_threshold"
        elif features.get("error_rate", 0.0) >= 10.0:
            is_anom = True
            reason = "high_error_rate_threshold"
        elif features.get("server_cpu_percent", 0.0) >= 90.0:
            is_anom = True
            reason = "cpu_saturation_threshold"
        elif lat >= warn_lat:
            is_anom = True
            reason = "warning_latency_threshold"

        metadata = {
            "detector_state": "cold_start",
            "detector_version": "baseline-fallback-v1.0",
            "top_contributor": reason or "normal",
            "deviations": {k: round(v, 2) for k, v in features.items()}
        }
        return is_anom, 0.0 if not is_anom else -0.5, reason, metadata

    # --- Trained Multivariate Model Inference Path ---
    model = reg["model"]
    scaler = reg["scaler"]
    threshold = reg["threshold"]
    medians = reg["medians"]
    iqrs = reg["iqrs"]

    input_df = pd.DataFrame([features])[FEATURE_NAMES]
    scaled_vec = scaler.transform(input_df)

    # score_samples returns raw anomaly score (negative values; smaller = more anomalous)
    raw_score = float(model.score_samples(scaled_vec)[0])
    is_anomaly = bool(raw_score <= threshold)

    # Compute standardized feature deviation (distance in IQRs from median)
    deviations = {}
    for col in FEATURE_NAMES:
        med = medians.get(col, 0.0)
        iqr = iqrs.get(col, 1.0)
        val = features.get(col, 0.0)
        deviations[col] = (val - med) / iqr

    # Identify top feature contributor by positive deviation magnitude
    ranked_features = sorted(deviations.items(), key=lambda item: abs(item[1]), reverse=True)
    top_feature = ranked_features[0][0] if ranked_features else "p99_latency_ms"

    label = None
    if is_anomaly:
        if "latency" in top_feature:
            label = "latency_spike"
        elif "error" in top_feature:
            label = "error_rate_burst"
        elif "cpu" in top_feature:
            label = "cpu_saturation"
        elif "memory" in top_feature:
            label = "memory_pressure"
        elif "rps" in top_feature:
            label = "traffic_surge"
        else:
            label = f"{top_feature}_anomaly"

    metadata = {
        "detector_state": "model_ready",
        "detector_version": reg["version"],
        "anomaly_score": round(raw_score, 4),
        "score_threshold": round(threshold, 4),
        "top_contributor": top_feature,
        "ranked_deviations": [(k, round(v, 2)) for k, v in ranked_features]
    }

    return is_anomaly, raw_score, label, metadata

def generate_forecast(endpoint_id: int, steps: int = 10) -> list[float]:
    """Uses ARIMA to forecast the next `steps` response time values for an endpoint."""
    db = SessionLocal()
    try:
        results = db.query(MonitoringResult).filter(
            MonitoringResult.endpoint_id == endpoint_id,
            MonitoringResult.response_time_ms.isnot(None)
        ).order_by(MonitoringResult.timestamp.desc()).limit(100).all()

        results.reverse()
        if len(results) < 20:
            return []

        data = [r.response_time_ms for r in results]
        model = ARIMA(data, order=(1, 1, 1))
        model_fit = model.fit()
        forecast = model_fit.forecast(steps=steps)
        return [round(float(v), 2) for v in forecast.tolist()]

    except Exception as e:
        logger.error("Error generating ARIMA forecast for endpoint %s: %s", endpoint_id, e)
        return []
    finally:
        db.close()
