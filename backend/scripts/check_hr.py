"""Check database for HR metrics data."""

from app.core.database import SessionLocal
from app.models.models import Activity

db = SessionLocal()

try:
    # Count activities that have metrics_data
    activities_with_metrics = (
        db.query(Activity).filter(Activity.metrics_data.isnot(None)).count()
    )
    print(f"Activities with metrics data: {activities_with_metrics}")

    if activities_with_metrics > 0:
        metrics_activities = (
            db.query(Activity)
            .filter(Activity.metrics_data.isnot(None))
            .order_by(Activity.start_time.desc())
            .all()
        )
        for act in metrics_activities:
            hr_count = sum(1 for m in act.metrics_data if m.get("directHeartRate"))
            print(
                f"  {act.id}: {act.activity_type} - {act.start_time} "
                f"({hr_count} HR samples)"
            )
    else:
        print("No metrics data found in database")

        # Get all activities
        activities = (
            db.query(Activity).order_by(Activity.start_time.desc()).limit(5).all()
        )
        print(f"Recent activities:")
        for act in activities:
            has_metrics = "yes" if act.metrics_data else "no"
            print(
                f"  {act.id}: {act.activity_type} - {act.start_time} "
                f"(metrics: {has_metrics})"
            )
finally:
    db.close()
