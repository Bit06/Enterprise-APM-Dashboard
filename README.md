# Enterprise API & Application Performance Monitoring (APM) System

An intelligent, full-stack API and Application Performance Monitoring prototype designed for enterprise services and RESTful APIs. Combines synthetic health probing, real-time telemetry ingestion, **Multivariate Isolation Forest anomaly detection**, **Cold-Start statistical baselines**, **Multimodal Root Cause Analysis (RCA)**, and OpenTelemetry-based distributed tracing.

---

## Project Structure

```
apm_system/
├── app/
│   ├── main.py                  # FastAPI application: REST API & dashboard router
│   ├── monitoring.py            # Monitoring engine: scheduled probing & 1-min metric aggregation
│   ├── worker.py                # Decoupled telemetry worker consuming from in-memory queue
│   ├── ml_engine.py             # Multivariate Isolation Forest, Cold-Start fallback, ARIMA forecasting
│   ├── rca.py                   # Multimodal RCA engine (Table 5.4 diagnostic evidence schema)
│   ├── alerts.py                # Alert deduplication, SMTP email, and Microsoft Teams notifications
│   ├── models.py                # SQLAlchemy ORM database models
│   ├── schemas.py               # Pydantic request & response validation
│   └── database.py              # Database connection (SQLite by default, PostgreSQL/MSSQL ready)
├── static/
│   ├── index.html               # Web dashboard: executive KPIs, status grid, latency trend charts
│   └── endpoint.html            # Endpoint detail view: interactive latency trends, RCA modal
├── experiments/
│   ├── evaluate_chapter5.py     # Controlled-workload test harness (seed 20261125, 12,000 points)
│   └── evaluate_smd_benchmark.py# Server Machine Dataset (SMD) 38-dim benchmark runner
├── dummy_app.py                 # OpenTelemetry-instrumented target service with fault simulation (/_fault)
├── load_generator.py            # Async concurrent load generator (normal, latency_spike, error_burst)
├── seed_endpoints.py            # Registers sample endpoints for testing
├── docker-compose.yml           # Multi-container orchestration (OTel, Jaeger, Prometheus, APM)
├── otel-collector-config.yaml   # OpenTelemetry Collector routing configuration
├── prometheus.yml               # Prometheus scraping rules
├── Dockerfile                   # Container build recipe
├── requirements.txt             # Pinned project dependencies
├── chapter5_results.json        # Output of Chapter 5 controlled-workload evaluation
├── smd_benchmark_results.json   # Output of Server Machine Dataset (SMD) benchmark
└── PROJECT_IMPLEMENTATION_AND_EVALUATION_GUIDE.md # Master project reference & defense guide
```

---

## 1. Local Setup

```bash
cd apm_system
python -m venv venv

# Activate virtual environment:
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Windows (cmd):
venv\Scripts\activate.bat
# Linux / macOS:
source venv/bin/activate

pip install -r requirements.txt
```

---

## 2. Running the System (3 Terminals)

To run the complete interactive APM demonstration with live traffic and fault injection:

* **Terminal 1 (APM Backend Server):**
  ```bash
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
  ```
  Dashboard UI: **http://localhost:8000**  
  Interactive Swagger Docs: **http://localhost:8000/docs**

* **Terminal 2 (OpenTelemetry-Instrumented Target App):**
  ```bash
  uvicorn dummy_app:app --host 0.0.0.0 --port 8001
  ```

* **Terminal 3 (Traffic Generator):**
  ```bash
  python load_generator.py --mode normal
  ```

---

## 3. Running Academic Evaluation Suites

The repository contains reproducible evaluation scripts that validate the machine-learning models against threshold baselines:

### Chapter 5 Controlled-Workload Experiment
Reproduces **Table 5.2** (Confusion Matrix, Precision, Recall, F1, FPR, MTTD) and **Table 5.3** (Per-scenario delays & feature attribution) using seed `20261125` across 12,000 points and 6 injected failure scenarios:
```bash
python experiments/evaluate_chapter5.py
```
*Results are exported to `chapter5_results.json`.*

### Server Machine Dataset (SMD) Public Benchmark
Evaluates the Multivariate Isolation Forest against a PCA reconstruction error baseline across 38 continuous server metric dimensions (Su et al., 2019 / Alves et al., 2026):
```bash
python experiments/evaluate_smd_benchmark.py
```
*Results are exported to `smd_benchmark_results.json`.*

---

## 4. Docker Enterprise Deployment

To spin up the full observability stack including **OpenTelemetry Collector**, **Jaeger Tracing**, and **Prometheus**:
```bash
docker-compose up --build
```
* **APM Backend:** `http://localhost:8000`
* **Target Dummy App:** `http://localhost:8001`
* **Jaeger Tracing UI:** `http://localhost:16686`
* **Prometheus Dashboard:** `http://localhost:9090`
* **OTel Collector:** gRPC `4317` / HTTP `4318`

---

## 5. Machine Learning & Anomaly Detection Details

* **Multivariate Features:** Evaluates `[rps, p95_latency_ms, p99_latency_ms, error_rate, server_cpu_percent, server_memory_percent]` simultaneously.
* **Leakage-Free Scaling:** Fits `RobustScaler` only on chronological training windows.
* **Cold-Start Fallback:** Automatically operates in `cold_start` mode using robust rolling medians/IQRs and operational thresholds when historical samples are `< 25`.
* **Explainability:** Computes standardized deviations to identify and rank the primary contributing feature behind every detected anomaly.
* **Forecasting:** Uses ARIMA(1, 1, 1) on response times to project forward latency trends.

---

## 6. Root Cause Analysis (RCA) Engine

When an incident occurs, the RCA engine (`app/rca.py`) evaluates broken telemetry against the **Table 5.4 Multimodal Evidence schema**:
1. **Service Offline:** Unreachable endpoint / connection refused patterns.
2. **CPU Saturation:** Server CPU > 85% with peak spikes.
3. **Memory Exhaustion:** Server RAM > 85%.
4. **Internal Server Error:** HTTP 500 error percentage > 30%.
5. **Severe Latency Spike:** Average response time exceeding warning/critical limits.
6. **Correlated Evidence:** Returns W3C trace identifiers, raw error logs, and confidence notes.

---

## 7. Switching the Database & Configuring Alerts

### Database Dialect Switch
By default, the app uses SQLite (`apm_system.db`). To point at PostgreSQL or SQL Server, set `DATABASE_URL`:
```bash
# PostgreSQL
export DATABASE_URL="postgresql+psycopg2://user:password@localhost:5432/apm_db"
# SQL Server
export DATABASE_URL="mssql+pyodbc://user:password@your_dsn_name"
```

### Alert Notifications
Configure email (SMTP) and Microsoft Teams webhooks via environment variables:
```bash
export SMTP_HOST="smtp.office365.com"
export SMTP_PORT=587
export SMTP_USER="apm-alerts@company.com"
export SMTP_PASSWORD="password"
export ALERT_EMAIL_TO="ops-team@company.com"
export TEAMS_WEBHOOK_URL="https://yourcompany.webhook.office.com/..."
```
If unset, alerts are logged to the console without interrupting execution.

---

## 8. Complete Project & Defense Guide

For comprehensive documentation, code tours, and defense scripts, refer to:
👉 **[`PROJECT_IMPLEMENTATION_AND_EVALUATION_GUIDE.md`](PROJECT_IMPLEMENTATION_AND_EVALUATION_GUIDE.md)**
