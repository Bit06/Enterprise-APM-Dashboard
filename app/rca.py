import re
from sqlalchemy.orm import Session
from datetime import datetime
from app.models import Incident, MonitoringResult

def analyze_incident_root_cause(db: Session, incident_id: int):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        return None
        
    end_time = incident.resolution_time or datetime.utcnow()
    
    # Query all monitoring results in the incident window for this endpoint
    results = (
        db.query(MonitoringResult)
        .filter(
            MonitoringResult.endpoint_id == incident.endpoint_id,
            MonitoringResult.timestamp >= incident.start_time,
            MonitoringResult.timestamp <= end_time
        )
        .order_by(MonitoringResult.timestamp.asc())
        .all()
    )
    
    if not results:
        # Fallback if no records
        return {
            "incident_id": incident.id,
            "rca_analysis": [{
                "rule": "undetermined",
                "confidence": "low",
                "evidence": "No monitoring records found in incident window",
                "threshold": 0.0
            }],
            "telemetry_snapshot": []
        }
    
    rca_analysis = []
    total_checks = len(results)
    
    # 1. Service Offline
    # Require >= 80% of checks to have status_code IS NULL
    none_count = sum(1 for r in results if r.status_code is None)
    if total_checks > 0 and (none_count / total_checks) >= 0.8:
        conn_patterns = [
            r"ConnectionRefused", r"ConnectionTimeout", r"DNS", 
            r"Name or service not known", r"timed out", r"ECONNRESET",
            r"Max retries exceeded"
        ]
        conn_errors_count = sum(
            1 for r in results 
            if r.error_message and any(re.search(pat, r.error_message, re.IGNORECASE) for pat in conn_patterns)
        )
        if conn_errors_count > 0:
            rca_analysis.append({
                "rule": "Service Offline",
                "confidence": "probable",
                "evidence": f"{none_count}/{total_checks} checks failed to connect.",
                "threshold": 0.8
            })
            
    # Calculate averages (filter out None values which happen when service is down or metrics fail)
    cpu_values = [r.server_cpu_percent for r in results if r.server_cpu_percent is not None]
    mem_values = [r.server_memory_percent for r in results if r.server_memory_percent is not None]
    
    # 2. CPU Saturation
    if cpu_values:
        avg_cpu = sum(cpu_values) / len(cpu_values)
        if avg_cpu > 90.0:
            rca_analysis.append({
                "rule": "CPU Saturation",
                "confidence": "probable",
                "evidence": f"Avg CPU {avg_cpu:.1f}% over {len(cpu_values)} successful metric fetches.",
                "threshold": 90.0
            })
            
    # 3. Memory Pressure
    if mem_values:
        avg_mem = sum(mem_values) / len(mem_values)
        if avg_mem > 85.0:
            rca_analysis.append({
                "rule": "Memory Exhaustion",
                "confidence": "probable",
                "evidence": f"Avg Memory {avg_mem:.1f}% over {len(mem_values)} successful metric fetches.",
                "threshold": 85.0
            })
            
    # 4. Upstream Errors (500s)
    error_500_count = sum(1 for r in results if r.status_code == 500)
    if total_checks > 0 and (error_500_count / total_checks) > 0.5:
        rca_analysis.append({
            "rule": "Internal Server Error",
            "confidence": "indicated",
            "evidence": f"{error_500_count}/{total_checks} checks returned 500.",
            "threshold": 0.5
        })

    # Sort rules by priority: Service Offline > CPU > Memory > Internal Server Error
    priority_map = {
        "Service Offline": 1,
        "CPU Saturation": 2,
        "Memory Exhaustion": 3,
        "Internal Server Error": 4
    }
    rca_analysis.sort(key=lambda x: priority_map.get(x["rule"], 99))
    
    # Fallback when zero rules fire
    if not rca_analysis:
        rca_analysis.append({
            "rule": "undetermined",
            "confidence": "low",
            "evidence": "No threshold exceeded",
            "threshold": 0.0
        })
        
    # Telemetry Snapshot Overlap bug fix
    if len(results) <= 10:
        snapshot = results
    else:
        snapshot = results[:5] + results[-5:]
        
    return {
        "incident_id": incident.id,
        "rca_analysis": rca_analysis,
        "telemetry_snapshot": snapshot
    }
