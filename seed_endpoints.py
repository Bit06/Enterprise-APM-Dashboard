"""
Registers a few sample endpoints so you can see the system working
immediately without setting up your own test targets first.

Run this AFTER the server is up:
    python seed_endpoints.py
"""
import requests

BASE = "http://localhost:8000"

samples = [
    {
        "name": "Public Test API (httpbin)",
        "url": "https://httpbin.org/get",
        "environment": "external-test",
        "check_interval_seconds": 30,
        "timeout_seconds": 5,
        "response_time_warn_ms": 800,
        "response_time_critical_ms": 2000,
        "consecutive_failures_for_alert": 2,
    },
    {
        "name": "Simulated Slow Endpoint",
        "url": "https://httpbin.org/delay/2",
        "environment": "external-test",
        "check_interval_seconds": 60,
        "timeout_seconds": 10,
        "response_time_warn_ms": 500,
        "response_time_critical_ms": 1500,
        "consecutive_failures_for_alert": 2,
    },
    {
        "name": "Simulated 500 Error Endpoint",
        "url": "https://httpbin.org/status/500",
        "environment": "external-test",
        "check_interval_seconds": 30,
        "timeout_seconds": 5,
        "response_time_warn_ms": 1000,
        "response_time_critical_ms": 3000,
        "consecutive_failures_for_alert": 1,
    },
]

for ep in samples:
    r = requests.post(f"{BASE}/api/endpoints", json=ep)
    print(ep["name"], "->", r.status_code, r.json() if r.ok else r.text)
