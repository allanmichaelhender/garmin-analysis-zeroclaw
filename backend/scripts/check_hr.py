"""Check database for HR data."""

from app.core.database import SessionLocal
from app.models.models import Activity, HeartRateData

db = SessionLocal()

try:
    hr_count = db.query(HeartRateData).count()
    print(f'Total HR data points: {hr_count}')
    
    if hr_count > 0:
        activity_ids = db.query(HeartRateData.activity_id).distinct().all()
        print(f'Activities with HR data: {[a[0] for a in activity_ids]}')
        
        # Get most recent activity with HR data
        latest_activity_id = activity_ids[0][0]
        activity = db.query(Activity).filter(Activity.id == latest_activity_id).first()
        print(f'Most recent activity with HR: {activity.id} - {activity.activity_type} - {activity.start_time}')
    else:
        print('No HR data in database')
        
        # Get all activities
        activities = db.query(Activity).order_by(Activity.start_time.desc()).limit(5).all()
        print(f'Recent activities:')
        for act in activities:
            print(f'  {act.id}: {act.activity_type} - {act.start_time}')
finally:
    db.close()
