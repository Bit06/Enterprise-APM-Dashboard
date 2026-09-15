# Simplified APM System Architecture

This document serves as the master reference for your project defense, explaining the architecture of the Enterprise APM Dashboard in simple terms.

## 1. System Architecture Diagram

`mermaid
graph TD
    A[Monitoring Engine] -->|Pings & Collects Metrics| B((Target APIs))
    A -->|Raw Telemetry| C[Machine Learning]
    C -->|Anomaly Scores| D[(Time-Series DB)]
    A -->|Uptime Data| D
    D --> E[FastAPI Backend]
    E -->|Real-Time Data| F[Dashboard UI]
    E -->|Root Cause Analysis| F
`

## 2. Core Components

1. **Monitoring Engine (APScheduler):** Simulates real user traffic by pinging endpoints every 60 seconds to check health and response times.
2. **Machine Learning (Isolation Forest):** Analyzes response times dynamically to flag unusual latency spikes, preventing the need for static thresholds.
3. **Database (SQLite):** Acts as a local time-series database to store all historical telemetry and incidents.
4. **Backend (FastAPI):** Serves the API endpoints for the frontend and computes complex logic like Root Cause Analysis (RCA) and SLA percentages.
5. **Frontend (Vanilla JS):** Renders the metrics in a premium, real-time dashboard using Chart.js.

---

## 3. Root Cause Analysis (RCA)
When an endpoint fails, the RCA Engine checks the broken telemetry against 4 simple rules to find the exact cause:
1. **Service Offline:** The API completely stopped responding.
2. **CPU Saturation:** The server's CPU spiked above 85%.
3. **Memory Exhaustion:** The server ran out of RAM (>85%).
4. **Internal Server Error:** The API returned 500-level HTTP errors.

---

## 4. Defense Demo Script (How to wow the panel)

**Step 1: The Baseline**
Open the dashboard and point out that traffic is flowing normally and the global SLA is high.

**Step 2: Machine Learning in Action**
Switch your load generator to latency_spike mode. Wait 60 seconds. Point to the **Red Dots** on the dashboard charts and explain: *"Our ML model caught the latency spike dynamically before it ever hit a hard limit. This proves a faster Mean Time to Detect (MTTD)."*

**Step 3: Root Cause Analysis (RCA)**
Stop the dummy app completely. Wait for the SLA to drop. Open the details page for the app, click **Analyze Root Cause**, and show the panel how the system correctly identifies **Service Offline** instead of just throwing generic errors.
