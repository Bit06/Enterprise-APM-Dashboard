import os

with open('app/models.py', 'r') as f:
    content = f.read()

# Add team_name to Endpoint
content = content.replace('consecutive_failures_for_alert = Column(Integer, default=2)\n    is_active = Column(Boolean, default=True)\n    created_at = Column(DateTime, default=datetime.utcnow)\n\n    results', 'consecutive_failures_for_alert = Column(Integer, default=2)\n    is_active = Column(Boolean, default=True)\n    created_at = Column(DateTime, default=datetime.utcnow)\n    team_name = Column(String(100), nullable=True)\n\n    results')
content = content.replace('intervals = relationship("EndpointInterval", back_populates="endpoint", cascade="all, delete-orphan")', 'intervals = relationship("EndpointInterval", back_populates="endpoint", cascade="all, delete-orphan")\n    incidents = relationship("Incident", back_populates="endpoint", cascade="all, delete-orphan")')

# Add Incident model
incident_model = '''

class Incident(Base):
    \"\"\"A tracked lifecycle of an outage or severe degradation.\"\"\"
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    endpoint_id = Column(Integer, ForeignKey("endpoints.id"), nullable=False, index=True)
    status = Column(String(20), default="open") # open, resolved
    severity = Column(String(20), default="critical") # e.g. critical, warning
    start_time = Column(DateTime, default=datetime.utcnow, index=True)
    resolution_time = Column(DateTime, nullable=True)
    duration_minutes = Column(Float, nullable=True)
    assigned_team = Column(String(100), nullable=True)
    root_cause = Column(String(500), nullable=True)
    error_message = Column(Text, nullable=True)

    endpoint = relationship("Endpoint", back_populates="incidents")
'''
content = content.replace('endpoint = relationship("Endpoint", back_populates="alerts")\n\n\nclass EndpointInterval', 'endpoint = relationship("Endpoint", back_populates="alerts")' + incident_model + '\n\nclass EndpointInterval')

with open('app/models.py', 'w') as f:
    f.write(content)
print("Updated models.py")
