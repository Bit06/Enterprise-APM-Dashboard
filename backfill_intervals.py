import sys
import os

# Add the parent directory to sys.path so we can import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base, SessionLocal
from app.models import Endpoint, MonitoringResult, EndpointInterval

def backfill():
    # 1. Create the new table if it doesn't exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Clear existing intervals to avoid duplicates if run multiple times
        db.query(EndpointInterval).delete()

        endpoints = db.query(Endpoint).all()
        
        for ep in endpoints:
            results = (
                db.query(MonitoringResult)
                .filter(MonitoringResult.endpoint_id == ep.id)
                .order_by(MonitoringResult.timestamp.asc())
                .all()
            )

            if not results:
                continue

            current_status = 'up' if results[0].is_available else 'down'
            interval_start = results[0].timestamp
            last_timestamp = results[0].timestamp

            for r in results[1:]:
                status = 'up' if r.is_available else 'down'
                if status != current_status:
                    # Status changed, close previous interval
                    duration = (last_timestamp - interval_start).total_seconds()
                    db.add(EndpointInterval(
                        endpoint_id=ep.id,
                        status=current_status,
                        start_time=interval_start,
                        end_time=last_timestamp,
                        duration_seconds=duration
                    ))
                    
                    # Start new interval
                    current_status = status
                    interval_start = r.timestamp
                last_timestamp = r.timestamp

            # Close the final open interval
            duration = (last_timestamp - interval_start).total_seconds()
            db.add(EndpointInterval(
                endpoint_id=ep.id,
                status=current_status,
                start_time=interval_start,
                end_time=last_timestamp,
                duration_seconds=duration
            ))

        db.commit()
        print("Backfill complete!")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    backfill()
