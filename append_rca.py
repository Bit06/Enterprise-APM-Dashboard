with open('app/main.py', 'a', encoding='utf-8') as f:
    f.write('''
from app.rca import analyze_incident_root_cause

@app.get("/api/incidents/{incident_id}/rca", response_model=schemas.IncidentRCAOut)
def get_incident_rca(incident_id: int, db: Session = Depends(get_db)):
    result = analyze_incident_root_cause(db, incident_id)
    if not result:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Incident not found")
    return result
''')
print('Appended /rca endpoint to main.py')
