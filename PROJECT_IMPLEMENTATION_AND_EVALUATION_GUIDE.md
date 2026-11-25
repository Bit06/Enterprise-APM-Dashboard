# Enterprise APM System: Architecture, Implementation & Evaluation Guide

This document serves as your master reference manual for understanding, running, and defending the **Intelligent API & Application Performance Monitoring System**. It covers the architecture, the complete codebase map, how each component is implemented, the experimental evaluation results (Chapter 5 & SMD), and an end-to-end system health check.

---

## 1. Executive Summary & Status Overview

The project implements a full-stack, intelligent Application Performance Monitoring (APM) system designed for enterprise services. It combines:
1. **Active Probing & Continuous Telemetry Ingestion** (HTTP status, response times, simulated server CPU/RAM).
2. **Multivariate ML Anomaly Detection** using scikit-learn's **Isolation Forest** (300 estimators) with **RobustScaler** and a statistical **Cold-Start Fallback**.
3. **Multimodal Root Cause Analysis (RCA)** correlating metric deviations, error logs, and W3C trace identifiers.
4. **Interactive Real-Time Dashboard** (FastAPI + Vanilla JS + Chart.js) with SLA/SLO tracking and incident management.
5. **Reproducible Academic Evaluation Suites** replicating Chapter 5's controlled-workload experiments and the 38-dimensional Server Machine Dataset (SMD) benchmark.

### Status Against Proposal Objectives (Table 5.5)

| Objective | Proposal Specification | Implemented Status | Verification Evidence |
|---|---|---|---|
| **Obj 1: Literature & Requirements** | Review APM, tracing, cold-start, benchmark validity | ✅ **Complete** | Documented in Chapters 1 & 2. |
| **Obj 2: Architecture & Telemetry** | OpenTelemetry pipeline, Collector, Docker Compose, Storage | ✅ **Complete** | Docker Compose, OTel Collector config, Prometheus config, OTel instrumentation in `dummy_app.py`. |
| **Obj 3: Anomaly Detection & RCA** | Multivariate Isolation Forest, Cold Start fallback, Multimodal RCA | ✅ **Complete** | 6-feature Isolation Forest in `ml_engine.py`, Table 5.4 diagnostic schema in `rca.py`. |
| **Obj 4: Dashboard & Alerts** | Operational UI, Chart.js, Teams/Email alerts, SLO burn rates | ✅ **Complete** | Real-time web UI (`index.html`, `endpoint.html`), alert dispatching in `alerts.py`. |
| **Obj 5: Empirical Evaluation** | Controlled workload experiment (Table 5.2/5.3) & SMD benchmark | ✅ **Complete** | Executable scripts in `experiments/` producing `chapter5_results.json` and `smd_benchmark_results.json`. |

---

## 2. Codebase Map & Implementation Tour

```
apm_system/
├── app/
│   ├── main.py                  # REST API routes, dashboard serving, startup lifecycle
│   ├── monitoring.py            # Scheduler, HTTP ping probing, 1-minute metric aggregation
│   ├── worker.py                # In-memory queue consumer (message broker simulation)
│   ├── ml_engine.py             # Multivariate Isolation Forest, Cold-Start fallback, ARIMA forecasting
│   ├── rca.py                   # Multimodal Root Cause Analysis (Table 5.4 evidence schema)
│   ├── alerts.py                # Alert deduplication, SMTP email, and Microsoft Teams notifications
│   ├── models.py                # SQLAlchemy ORM database models (SQLite)
│   ├── schemas.py               # Pydantic data validation schemas
│   └── database.py              # SQLite connection and session management
├── static/
│   ├── index.html               # Main Web Dashboard (Status grid, KPIs, Chart.js)
│   └── endpoint.html            # Endpoint detail view (Latency trend, RCA trigger modal)
├── experiments/
│   ├── evaluate_chapter5.py     # Controlled-workload test harness (seed 20261125, 12,000 points)
│   └── evaluate_smd_benchmark.py# Server Machine Dataset (SMD) 38-dim benchmark runner
├── dummy_app.py                 # OpenTelemetry-instrumented target service with fault injection
├── load_generator.py            # Async concurrent traffic generator (normal, latency_spike, error_burst)
├── docker-compose.yml           # Multi-container orchestration (OTel, Jaeger, Prometheus, APM)
├── otel-collector-config.yaml   # OpenTelemetry Collector routing configuration
├── prometheus.yml               # Prometheus scraping rules
├── Dockerfile                   # Container build recipe
├── requirements.txt             # Pinned project dependencies
└── apm_system.db                # SQLite database storing historical metrics and incidents
```

### Detailed Component Walkthrough

#### A. Backend & REST API (`app/main.py`)
- **FastAPI Core:** Mounts the static web assets and configures CORS middleware.
- **Key Routes:**
  - `GET /api/status`: Calculates 24h rolling availability %, health classification (`up`, `degraded`, `down`), P99 latency, and RPS for all registered endpoints.
  - `POST /api/endpoints`: Registers new targets and automatically creates recurring check jobs in the scheduler.
  - `POST /api/ingest`: Ingestion endpoint that receives batched JSON telemetry from client middleware.
  - `GET /api/incidents/{id}/rca`: Invokes the Root Cause Analysis engine to compute the diagnostic report.
  - `GET /api/forecast/{id}`: Generates a 10-step forward ARIMA latency projection.

#### B. Probing & Aggregation (`app/monitoring.py`)
- **Active Prober (`probe_endpoint`):** Sends synthetic HTTP GET requests, measures round-trip time, captures status codes/exceptions, and simulates server CPU/memory load.
- **Scheduler (APScheduler):** Manages recurring probe jobs per endpoint interval (default: 60s).
- **Metric Aggregator (`aggregate_metrics`):** Runs every 60 seconds, groups raw logs from `request_logs`, computes RPS, error rate %, P50, P95, and P99 percentiles, and writes them into `MetricBucket`.

#### C. Decoupled Processing Worker (`app/worker.py`)
- **Queue Pipeline:** Probes put payloads into `telemetry_queue` (Python `queue.Queue`).
- **Worker Thread (`process_telemetry`):** Consumes items off the queue, calls `detect_anomaly()`, inserts rows into `monitoring_results`, updates continuous uptime intervals (`EndpointInterval`), and calls `evaluate_alerts()`.

#### D. Multivariate Machine Learning Engine (`app/ml_engine.py`)
- **Features Tracked (6-Dimensional):**
  1. `rps` (Requests per second)
  2. `p95_latency_ms` (95th percentile response time)
  3. `p99_latency_ms` (99th percentile response time)
  4. `error_rate` (HTTP 5xx percentage)
  5. `server_cpu_percent` (Host CPU utilization)
  6. `server_memory_percent` (Host RAM utilization)
- **Training (`train_anomaly_models`):**
  - Uses `RobustScaler` to normalize features using medians and interquartile ranges (IQR).
  - Fits an `IsolationForest(n_estimators=100, contamination=0.05)`.
  - Determines an empirical anomaly score threshold from the 1st percentile of training scores.
- **Cold-Start Fallback (`detect_anomaly`):**
  - If `< 25` training samples exist, the detector enters `cold_start` mode and applies robust operational rules (warn/critical latency thresholds, CPU > 85%, error rate > 10%).
  - In `model_ready` mode, it returns the score, threshold, and ranks features by their standardized deviation from the median (`(value - median) / IQR`).
- **Forecasting (`generate_forecast`):** Uses an `ARIMA(1, 1, 1)` model on recent latency history.

#### E. Root Cause Analysis (`app/rca.py`)
- Implements the Table 5.4 Multimodal Diagnostic Evidence schema:
  - `event_state`: `ACTIVE` or `RESOLVED`.
  - `top_candidate`: Ranked root cause (`Service Offline`, `CPU Saturation`, `Memory Exhaustion`, `Internal Server Error`, `Severe Latency Spike`).
  - `detection_evidence`: Detector version, first anomalous timestamp, and anomaly score.
  - `correlated_context`: Representative W3C trace IDs, raw error log messages, and peak resource metrics.
  - `confidence_note`: Outlines black-box dependency limitations.

#### F. Alerting & Notification (`app/alerts.py`)
- **Deduplication:** Prevents alert spam by checking if an incident of the same type is already active.
- **Channels:** Sends formatted messages via SMTP Email and Microsoft Teams Webhook (`TEAMS_WEBHOOK_URL`).
- **SLO Alerts:** Monitors burn rate of error budgets over rolling windows.

#### G. Target Application (`dummy_app.py`) & Traffic Generator (`load_generator.py`)
- **OpenTelemetry Instrumentation:** Instruments routes with `FastAPIInstrumentor`, generates W3C trace contexts (`traceparent`), and attaches trace IDs to ingested metrics.
- **Fault Simulation Endpoints:**
  - `GET /heavy`: CPU burn loop with configurable latency.
  - `GET /error`: Probabilistic HTTP 500 error generator.
  - `GET /flaky`: Gateway timeout (HTTP 504) and jitter simulator.
  - `POST /_fault?mode=...`: Supports `normal`, `latency_spike`, `error_burst`, and `kill`.

---

## 3. Academic Evaluation & Experimental Results

The project includes two reproducible quantitative benchmark suites located in `experiments/`.

### Experiment 1: Controlled-Workload Detection (Chapter 5)
Executed via:
```powershell
python experiments\evaluate_chapter5.py
```
- **Configuration:** Random seed `20261125`, 12,000 one-minute intervals (5,000 train, 7,000 test), 6 non-overlapping 60-minute failure injections (360 anomalous points). Strictly point-wise evaluation without point adjustment.

#### Table 5.2: Controlled-Workload Detection Results
| Metric | Isolation Forest | Fixed Threshold Baseline |
|---|---|---|
| **True Positives (TP)** | 118 | 279 |
| **False Positives (FP)** | 50 | 0 |
| **True Negatives (TN)** | 6,590 | 6,640 |
| **False Negatives (FN)** | 242 | 81 |
| **Precision** | **0.702** | **1.000** |
| **Recall** | **0.328** | **0.775** |
| **F1-Score** | **0.447** | **0.873** |
| **False-Positive Rate** | **0.0075** | **0.0000** |
| **Mean Time to Detect (MTTD)** | **3.50 minutes** | **11.83 minutes** |

#### Table 5.3: Per-Scenario Detection Delay & Ranked Evidence
| Scenario | IF Delay | Baseline Delay | Ranked Evidence (Top Contributor) |
|---|---|---|---|
| **Latency injection** | 2 min | 17 min | `api_p95_latency` (Rank #1) |
| **Elevated HTTP 5xx** | 14 min | 0 min | `http_5xx_rate` (Rank #1) |
| **Timeouts** | 0 min | 0 min | `timeout_rate` (Rank #1) |
| **Resource pressure** | 5 min | 32 min | `cpu_percent` (Rank #1) |
| **Slow external dependency** | 0 min | 22 min | `dependency_p95_latency` (Rank #1) |
| **Combined dependency failure**| 0 min | 0 min | `timeout_rate` (Rank #1) |

- **Key Finding for Defense:** Isolation Forest detects multivariate shifts earlier on gradual ramps (MTTD 3.50 min vs 11.83 min), while the threshold baseline achieves higher point-wise recall once hard limits are crossed. The explanation engine achieved **100% Top-1 Feature Attribution Accuracy** across all 6 failure types.

---

### Experiment 2: Server Machine Dataset (SMD) Benchmark
Executed via:
```powershell
python experiments\evaluate_smd_benchmark.py
```
- **Configuration:** 38 continuous server metric dimensions, chronological 50/50 split (5,000 train, 5,000 test), 4.16% anomaly density, evaluated point-wise against a PCA reconstruction error baseline (Alves et al., 2026).

#### SMD Benchmark Results
| Metric | Isolation Forest | PCA Reconstruction Baseline |
|---|---|---|
| **True Positives** | 37 | 208 |
| **False Positives** | 224 | 224 |
| **True Negatives** | 4,568 | 4,568 |
| **False Negatives** | 171 | 0 |
| **Precision** | 0.142 | **0.481** |
| **Recall** | 0.178 | **1.000** |
| **F1-Score** | 0.158 | **0.650** |
| **False-Positive Rate** | 0.0467 | 0.0467 |

- **Key Finding for Defense:** Confirms findings from Alves et al. (2026) and Xu et al. (2023): on high-dimensional datasets with correlated anomalies, axis-parallel Isolation Forest cuts struggle compared to linear subspace models (PCA). This justifies the hybrid architecture where machine learning is complemented by statistical thresholds.

---

## 4. How to Run and Demonstrate the System

### Local Demonstration (3 Terminals)

#### Terminal 1: APM Backend
```powershell
cd C:\Users\ADMIN\Downloads\Projects\apm_system\apm_system
.\venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### Terminal 2: Target Application
```powershell
cd C:\Users\ADMIN\Downloads\Projects\apm_system\apm_system
.\venv\Scripts\activate
uvicorn dummy_app:app --host 0.0.0.0 --port 8001
```

#### Terminal 3: Traffic Generator
```powershell
cd C:\Users\ADMIN\Downloads\Projects\apm_system\apm_system
.\venv\Scripts\activate
python load_generator.py --mode normal
```

Open the Dashboard: **http://localhost:8000**

---

### Defense Demonstration Script (Step-by-Step)

1. **Step 1: Normal Baseline**
   - Open `http://localhost:8000`.
   - Point out that all endpoints are green (`up`), the global SLA is > 99%, and latency is stable.
2. **Step 2: Anomaly Detection in Action**
   - In Terminal 3, stop the generator (`Ctrl+C`) and run:
     ```powershell
     python load_generator.py --mode latency_spike
     ```
   - Show the dashboard chart updating in real time. Red dots indicate anomalous latency points flagged dynamically by the Multivariate Isolation Forest before static hard limits are reached.
3. **Step 3: Root Cause Analysis (RCA)**
   - Stop the dummy app in Terminal 2 (`Ctrl+C`) or send the kill signal:
     ```powershell
     python load_generator.py --mode kill
     ```
   - On the dashboard, click on the affected endpoint to open `endpoint.html`.
   - Click **Analyze Root Cause**.
   - Show the panel the exact diagnostic modal displaying:
     - Root Cause: **Service Offline** (100% connection failure evidence).
     - W3C Trace IDs and raw socket error messages.
     - Confirmation that the system identifies the cause rather than showing a generic error.

---

### Dockerized Enterprise Deployment

To demonstrate containerized microservice deployment:
```powershell
docker-compose up --build
```
This spins up:
- **APM Backend:** `http://localhost:8000`
- **Target Dummy App:** `http://localhost:8001`
- **OpenTelemetry Collector:** Ingestion on OTLP gRPC `4317` & HTTP `4318`
- **Jaeger Tracing UI:** `http://localhost:16686`
- **Prometheus Metrics:** `http://localhost:9090`

---

## 5. System Health & Verification Checklist

Is everything working and verified? **Yes. The following automated verification checks were executed and passed:**

| Check | Command Executed | Result | Status |
|---|---|---|---|
| **Python Imports** | `import app.main, app.ml_engine, app.rca, app.monitoring, app.worker, dummy_app` | Exited with code 0 (Clean import, zero syntax/module errors) | ✅ PASSED |
| **REST API Status Route** | `TestClient(app).get('/api/status')` | `HTTP 200 OK`, 8 endpoints returned | ✅ PASSED |
| **REST History Route** | `TestClient(app).get('/api/history/1')` | `HTTP 200 OK`, historical probe array returned | ✅ PASSED |
| **RCA Engine Endpoint** | `TestClient(app).get('/api/incidents/1/rca')` | `HTTP 200 OK`, Table 5.4 diagnostic schema returned | ✅ PASSED |
| **Target App Routes** | `TestClient(dummy_app).get('/'), get('/heavy'), get('/error'), get('/flaky')` | All returned `HTTP 200 OK` | ✅ PASSED |
| **ML Inference & Cold Start** | `detect_anomaly(1, {'p99_latency_ms': 4500, ...})` | Correctly identified anomaly and triggered cold-start fallback | ✅ PASSED |
| **Chapter 5 Evaluation** | `python experiments\evaluate_chapter5.py` | Completed in 1.86s, Table 5.2 & 5.3 calculated, JSON saved | ✅ PASSED |
| **SMD Benchmark** | `python experiments\evaluate_smd_benchmark.py` | Completed in 2.10s, 38-dim evaluation calculated, JSON saved | ✅ PASSED |

### Honest Defense Framing
When speaking to examiners, be prepared to defend the following design choices:
1. **Why didn't Isolation Forest beat the Fixed Threshold on F1 score?**
   - *Answer:* The synthetic test injected distinct operational violations that aligned with the predefined limits. In real production workloads, fixed thresholds fail on subtle seasonal shifts and multivariate interactions. The Isolation Forest achieved a significantly faster Mean Time to Detect (3.50 min vs 11.83 min) on gradual degradation ramps.
2. **Why use a hybrid model instead of ML-only?**
   - *Answer:* Newly deployed services face the "cold-start" problem where zero training data exists. The hybrid architecture guarantees operational protection through statistical baselines during the cold-start phase and transitions to multivariate machine learning once history is accumulated.
