# Enterprise APM System - Setup & Demo Guide

Follow these instructions to download, install, and run the complete APM Demonstration Environment on your local machine.

## 1. Prerequisites

Before you begin, ensure you have the following installed on your system:
- **Git:** To download the code. ([Download Git](https://git-scm.com/downloads))
- **Python 3.9+**: To run the backend server. ([Download Python](https://www.python.org/downloads/)) 
  - *Note for Windows users:* Make sure to check the box **"Add Python to PATH"** during installation.

## 2. Download the Source Code

Open your computer's terminal (Command Prompt or PowerShell on Windows, Terminal on Mac/Linux) and run the following command to download the folder from GitHub:

`ash
git clone https://github.com/Bit06/Enterprise-APM-Dashboard.git
`

Once downloaded, navigate into the project folder:
`ash
cd Enterprise-APM-Dashboard
`

## 3. Set Up the Virtual Environment

It is highly recommended to use a Python virtual environment to install the required dependencies so they do not conflict with other software on your computer.

**For Windows:**
`powershell
python -m venv venv
.\venv\Scripts\activate
`

**For Mac / Linux:**
`ash
python3 -m venv venv
source venv/bin/activate
`
*(You should see (venv) appear at the start of your terminal prompt, indicating the environment is active).*

## 4. Install Dependencies

With the virtual environment active, install all the required Python packages (FastAPI, SQLAlchemy, Uvicorn, APScheduler, Scikit-Learn, etc.):

`ash
pip install -r requirements.txt
`

---

## 5. Run the Demo Environment (Crucial for Defense)

To fully demonstrate the capabilities of the APM system (including SLA calculations, ML anomaly detection, and Root Cause Analysis), you need to run **three separate processes simultaneously**. 

You will need to open **three separate terminal windows**. Ensure that the virtual environment is activated (.\venv\Scripts\activate) in **all three windows**.

### Terminal 1: Start the APM Backend
This is the core engine that collects metrics, evaluates ML models, and serves the dashboard.
`ash
uvicorn app.main:app --host 0.0.0.0 --port 8000
`

### Terminal 2: Start the Dummy Target App
This is the mock e-commerce application that we will be monitoring and intentionally breaking during the demo.
`ash
uvicorn dummy_app:app --host 0.0.0.0 --port 8001
`

### Terminal 3: Start the Traffic Generator
This script acts as thousands of users hitting the dummy app, generating the raw telemetry data required for the charts and SLA math.
`ash
python load_generator.py --mode normal
`
*(Note: You can stop this script at any time using Ctrl+C and run it in --mode latency_spike or --mode error_burst to demonstrate anomalies to the panel!)*

---

## 6. Access the Dashboard

Once all three processes are running smoothly, open your web browser (Chrome, Edge, Firefox, Safari) and go to:

🚀 **http://localhost:8000**

You will see the APM Dashboard interface actively capturing data from the load generator. 

## Troubleshooting

- **Processes Hanging:** If the dashboard stops updating or a script freezes, press Ctrl+C in the terminal to stop the process, and run the command again.
- **Port in Use Error:** If you get an error that port 8000 is already in use, you likely have another instance of the server running in the background. Close all terminal windows and start fresh.
