import time
import os
import random
import threading
import httpx
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import List, Dict

app = FastAPI(title="Dummy Target Application")

FAULT_MODE = "normal"
APM_INGEST_URL = "http://localhost:8000/api/ingest"

# APM Middleware Batching
request_batch: List[Dict] = []
batch_lock = threading.Lock()
last_flush_time = time.time()
FLUSH_INTERVAL = 1.5
BATCH_SIZE_LIMIT = 50

def flush_metrics():
    global request_batch, last_flush_time
    with batch_lock:
        if not request_batch:
            return
        payload = request_batch.copy()
        request_batch.clear()
        last_flush_time = time.time()
        
    try:
        # Fire and forget POST to the APM backend
        httpx.post(APM_INGEST_URL, json=payload, timeout=2.0)
    except Exception as e:
        print(f"Failed to flush metrics to APM: {e}")

class APMMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        status_code = 500
        
        # Don't trace the fault endpoint itself
        if request.url.path == "/_fault":
            return await call_next(request)
            
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as e:
            status_code = 500
            raise e
        finally:
            duration_ms = (time.time() - start_time) * 1000
            
            # Record metric
            metric = {
                "endpoint": str(request.url),
                "method": request.method,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "timestamp": start_time
            }
            
            global request_batch, last_flush_time
            with batch_lock:
                request_batch.append(metric)
                should_flush = len(request_batch) >= BATCH_SIZE_LIMIT or (time.time() - last_flush_time) >= FLUSH_INTERVAL
                
            if should_flush:
                # Flush in a background thread to avoid blocking the response
                threading.Thread(target=flush_metrics, daemon=True).start()

app.add_middleware(APMMiddleware)


@app.post("/_fault")
def set_fault(mode: str):
    global FAULT_MODE
    print(f"Switching fault mode to: {mode}")
    if mode == "kill":
        print("KILL SIGNAL RECEIVED. Crashing in 3 seconds...")
        threading.Timer(3.0, lambda: os._exit(1)).start()
        return {"status": "crashing"}
        
    FAULT_MODE = mode
    return {"active_mode": mode}


@app.get("/")
def fast_endpoint():
    return {"message": "Hello World"}


@app.get("/heavy")
def heavy_endpoint():
    """Sync endpoint to utilize the thread pool and prevent event loop deadlocks."""
    start = time.time()
    
    # Normal behavior: slight CPU burn (e.g. 50ms)
    burn_time = 0.05
    
    if FAULT_MODE == "latency_spike":
        # Simulate a severe bottleneck
        burn_time = 3.0
        
    while time.time() - start < burn_time:
        pass
        
    return {"status": "computed", "burn_time": burn_time}


@app.get("/error")
def error_endpoint():
    # Normal behavior: 5% error rate
    fail_chance = 0.05
    
    if FAULT_MODE == "error_burst":
        fail_chance = 0.80
        
    if random.random() < fail_chance:
        return Response(content="Internal Server Error", status_code=500)
    return {"status": "ok"}


@app.get("/flaky")
def flaky_endpoint():
    # Mix of slow and error
    time.sleep(random.uniform(0.1, 0.5))
    if random.random() < 0.2:
        return Response(content="Gateway Timeout", status_code=504)
    return {"status": "ok"}

# Background thread to ensure metrics are flushed even if traffic is low
def periodic_flush():
    while True:
        time.sleep(1)
        global last_flush_time, request_batch
        with batch_lock:
            should_flush = len(request_batch) > 0 and (time.time() - last_flush_time) >= FLUSH_INTERVAL
        if should_flush:
            flush_metrics()

threading.Thread(target=periodic_flush, daemon=True).start()
