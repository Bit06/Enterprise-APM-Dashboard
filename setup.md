# Enterprise APM System - Setup & Demonstration Guide

Follow these instructions to download, install, run, and evaluate the complete APM Demonstration Environment on your local machine.

---

## 1. Prerequisites

Before you begin, ensure you have the following installed on your system:
- **Git:** To manage the code repository ([Download Git](https://git-scm.com/downloads)).
- **Python 3.10+**: To run the backend and analytics engine ([Download Python](https://www.python.org/downloads/)).
  - *Note for Windows users:* Check the box **"Add Python to PATH"** during installation.
- *(Optional)* **Docker Desktop:** Required only if running the containerized microservice stack ([Download Docker](https://www.docker.com/products/docker-desktop/)).

---

## 2. Set Up the Virtual Environment & Dependencies

Open your terminal (PowerShell on Windows, Terminal on macOS/Linux) inside the project directory:

```powershell
cd apm_system

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Windows (Command Prompt):
venv\Scripts\activate.bat
# macOS / Linux:
source venv/bin/activate

# Install all dependencies (FastAPI, scikit-learn, OpenTelemetry, pandas, statsmodels, etc.)
pip install -r requirements.txt
```

*(You should see `(venv)` appear at the start of your terminal prompt).*

---

## 3. Run the Live Interactive Demo (3 Terminals)

To demonstrate real-time telemetry collection, SLA tracking, dynamic ML anomaly detection, and Root Cause Analysis, open **three separate terminal windows** with the virtual environment activated in all three.

### Terminal 1: Start the APM Backend Server
Starts the core monitoring engine, background worker, ML detector, and dashboard UI:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
- **Dashboard UI:** Open [http://localhost:8000](http://localhost:8000)
- **API Documentation (Swagger):** Open [http://localhost:8000/docs](http://localhost:8000/docs)

### Terminal 2: Start the OpenTelemetry Target Application
Starts the mock service with OpenTelemetry distributed tracing and failure endpoints:
```bash
uvicorn dummy_app:app --host 0.0.0.0 --port 8001
```

### Terminal 3: Start the Traffic & Load Generator
Simulates user traffic hitting the target application:
```bash
python load_generator.py --mode normal
```

---

## 4. Live Failure Injection Demonstration (For Your Defense Panel)

You can demonstrate dynamic incident handling live to your panel:

| Scenario | Command to run in Terminal 3 | What to observe on Dashboard |
|---|---|---|
| **Normal Traffic** | `python load_generator.py --mode normal` | Steady green badges, low latency (< 50ms), SLA > 99%. |
| **Latency Bottleneck** | `python load_generator.py --mode latency_spike` | Response times jump to 3000ms. **Red dots appear** on charts, proving the **Multivariate Isolation Forest** flags anomalies before hard thresholds breach. |
| **Error Burst** | `python load_generator.py --mode error_burst` | 80% HTTP 500 error rate injected. Error rate rises and alert triggers. |
| **Service Crash / Outage** | `python load_generator.py --mode kill` | The dummy app shuts down. Status turns **RED (Down)**. Open the details page and click **Analyze Root Cause** — the RCA engine correctly identifies **"Service Offline"** with connection error logs and W3C trace IDs. |

---

## 5. Running the Academic Evaluation Suites

To reproduce the scientific evaluation metrics from Chapters 3, 4, and 5 of the thesis:

### A. Chapter 5 Controlled-Workload Evaluation
Runs the 12,000-point experiment (seed `20261125`) comparing Isolation Forest against fixed operational thresholds across 6 failure injection types:
```bash
python experiments/evaluate_chapter5.py
```
- Outputs **Table 5.2** (Confusion matrix, Precision, Recall, F1, FPR, MTTD).
- Outputs **Table 5.3** (Per-scenario detection delay & feature attribution ranking).
- Saves results to `chapter5_results.json`.

### B. Server Machine Dataset (SMD) Benchmark
Runs point-wise evaluation across 38 continuous server metric dimensions (Su et al., 2019 / Alves et al., 2026):
```bash
python experiments/evaluate_smd_benchmark.py
```
- Compares Isolation Forest against PCA reconstruction error baselines.
- Saves results to `smd_benchmark_results.json`.

---

## 6. Dockerized Microservice Stack (Alternative)

If your examiners request to see containerized orchestration:
```bash
docker-compose up --build
```
This launches:
- **APM Backend:** `http://localhost:8000`
- **Target Dummy App:** `http://localhost:8001`
- **OpenTelemetry Collector:** Ingestion on OTLP gRPC `4317` / HTTP `4318`
- **Jaeger Tracing Web UI:** `http://localhost:16686`
- **Prometheus Metrics UI:** `http://localhost:9090`

---

## 7. Troubleshooting

- **Port in Use:** If port `8000` or `8001` is already in use, close any previously running terminal windows.
- **Missing Module:** Ensure your virtual environment is active (`.\venv\Scripts\activate`) before launching `uvicorn` or `python`.
- **Master Guide:** For complete architecture details, refer to [`PROJECT_IMPLEMENTATION_AND_EVALUATION_GUIDE.md`](PROJECT_IMPLEMENTATION_AND_EVALUATION_GUIDE.md).
