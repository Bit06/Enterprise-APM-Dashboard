# Enterprise APM Dashboard - Setup Guide

Welcome to the Enterprise APM Dashboard! This system includes a Python FastAPI backend, a background telemetry scheduler, and an HTML/JS frontend dashboard. 

Follow these instructions to download and run the system on your own machine or server.

## 1. Prerequisites

Before you begin, ensure you have the following installed on your system:
- **Git:** To download the code. ([Download Git](https://git-scm.com/downloads))
- **Python 3.9+**: To run the backend server. ([Download Python](https://www.python.org/downloads/)) 
  - *Note for Windows users:* Make sure to check the box **"Add Python to PATH"** during installation.

## 2. Download the Source Code

Open your computer's terminal (Command Prompt or PowerShell on Windows, Terminal on Mac/Linux) and run the following command to download the folder from GitHub:

```bash
git clone https://github.com/Bit06/Enterprise-APM-Dashboard.git
```

Once downloaded, navigate into the project folder:
```bash
cd Enterprise-APM-Dashboard
```

## 3. Set Up the Virtual Environment

It is highly recommended to use a Python virtual environment to install the required dependencies so they do not conflict with other software on your computer.

**For Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**For Mac / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```
*(You should see `(venv)` appear at the start of your terminal prompt, indicating the environment is active).*

## 4. Install Dependencies

With the virtual environment active, install all the required Python packages (FastAPI, SQLAlchemy, Uvicorn, APScheduler, etc.):

```bash
pip install -r requirements.txt
```

## 5. Run the Server

You are now ready to start the server! Run the following command:

```bash
uvicorn app.main:app --reload
```

When you see the message `Application startup complete.`, the server is running successfully!

## 6. Access the Dashboard

Open your favorite web browser (Chrome, Edge, Firefox, Safari) and go to:

👉 **http://localhost:8000**

You will see the APM Dashboard interface. You can begin adding endpoints to monitor right away.

---

## Important Notes on Hosting & Deployment

This system runs a **Background Scheduler** that pings your APIs every 60 seconds (even when you are not actively looking at the dashboard). 

Because of this 24/7 background activity requirement, **free "Serverless" hosting tiers (like Vercel or Render's Free Tier) are not recommended.** Free tiers usually "go to sleep" after 15 minutes of inactivity, which will cause your background API monitoring to stop completely until someone visits the site again to wake it up.

**Recommended Hosting Providers:**
If you want to deploy this to the internet so you can view it from anywhere, it is recommended to use a paid VPS (Virtual Private Server) or a persistent container service:
- **Render.com** (Starter Web Service: ~$7/month + a persistent disk for the SQLite database)
- **Railway.app** (Developer plan: ~$5/month)
- **DigitalOcean** (Basic Droplet: ~$4/month)
