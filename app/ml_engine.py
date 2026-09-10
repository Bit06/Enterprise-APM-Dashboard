import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest
from statsmodels.tsa.arima.model import ARIMA
import warnings

from .database import SessionLocal
from .models import Endpoint, MonitoringResult

logger = logging.getLogger("apm.ml_engine")

# Suppress statsmodels warnings for cleaner logs
warnings.filterwarnings("ignore")

# In-memory store for models
anomaly_models = {}

def train_anomaly_models():
    """Fetches recent historical data and trains an IsolationForest for each active endpoint."""
    logger.info("Training ML anomaly detection models...")
    db = SessionLocal()
    try:
        endpoints = db.query(Endpoint).filter(Endpoint.is_active == True).all()
        since = datetime.utcnow() - timedelta(days=7) # Use up to 7 days of data
        
        for ep in endpoints:
            results = db.query(MonitoringResult).filter(
                MonitoringResult.endpoint_id == ep.id,
                MonitoringResult.timestamp >= since,
                MonitoringResult.response_time_ms.isnot(None)
            ).all()
            
            if len(results) < 20:
                logger.info(f"Not enough data to train model for endpoint {ep.id} ({len(results)} samples).")
                continue
                
            # Prepare data
            df = pd.DataFrame([r.response_time_ms for r in results], columns=['response_time_ms'])
            
            # Train Isolation Forest (contamination=0.05 means we expect 5% anomalies)
            model = IsolationForest(contamination=0.05, random_state=42)
            model.fit(df[['response_time_ms']])
            
            anomaly_models[ep.id] = model
            logger.info(f"Successfully trained Isolation Forest for endpoint {ep.id} on {len(df)} samples.")
            
    except Exception as e:
        logger.error(f"Error training models: {e}")
    finally:
        db.close()

def detect_anomaly(endpoint_id: int, response_time_ms: float) -> tuple[bool, float]:
    """Scores a single telemetry point. Returns (is_anomaly, anomaly_score).
    Note: is_anomaly=True if score is negative in sklearn."""
    if response_time_ms is None or endpoint_id not in anomaly_models:
        return False, 0.0
        
    model = anomaly_models[endpoint_id]
    X = pd.DataFrame([response_time_ms], columns=['response_time_ms'])
    
    # Predict returns -1 for anomaly, 1 for normal
    prediction = model.predict(X)[0]
    # score_samples returns negative values; lower is more abnormal
    score = model.score_samples(X)[0]
    
    is_anomaly = bool(prediction == -1)
    return is_anomaly, float(score)

def generate_forecast(endpoint_id: int, steps: int = 10) -> list[float]:
    """Uses ARIMA to forecast the next `steps` response time values for an endpoint."""
    db = SessionLocal()
    try:
        # Get the last 100 data points to train the forecast model
        results = db.query(MonitoringResult).filter(
            MonitoringResult.endpoint_id == endpoint_id,
            MonitoringResult.response_time_ms.isnot(None)
        ).order_by(MonitoringResult.timestamp.desc()).limit(100).all()
        
        # Reverse to get chronological order
        results.reverse()
        
        if len(results) < 30:
            return [] # Need sufficient data to forecast
            
        data = [r.response_time_ms for r in results]
        
        # Fit ARIMA model (using a simple order (1,1,1) for the prototype)
        model = ARIMA(data, order=(1, 1, 1))
        model_fit = model.fit()
        
        # Forecast
        forecast = model_fit.forecast(steps=steps)
        return forecast.tolist()
        
    except Exception as e:
        logger.error(f"Error generating forecast for endpoint {endpoint_id}: {e}")
        return []
    finally:
        db.close()
