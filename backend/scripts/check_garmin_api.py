"""Check Garmin API structure for activity details."""

import os
from dotenv import load_dotenv
from app.clients.garmin import GarminClient
from app.core.database import SessionLocal
from app.models.models import Activity

load_dotenv()

email = os.getenv("GARMIN_EMAIL")
password = os.getenv("GARMIN_PASSWORD")

if not email or not password:
    print("GARMIN_EMAIL and GARMIN_PASSWORD not set")
    exit(1)

client = GarminClient(email, password)

# Get most recent activity ID from database
db = SessionLocal()
activity = db.query(Activity).order_by(Activity.start_time.desc()).first()
db.close()

if not activity:
    print("No activities found")
    exit(1)

print(f"Fetching details for activity {activity.id}")
activity_detail = client.get_activity_details(activity_id=activity.id)

print("\nActivity detail keys:")
print(list(activity_detail.keys()))

if "metricDescriptors" in activity_detail:
    print(f"\nmetricDescriptors count: {len(activity_detail['metricDescriptors'])}")
    print("All descriptors:")
    for i, desc in enumerate(activity_detail["metricDescriptors"]):
        print(f"  {i}: {desc}")

if "heartRateDTOs" in activity_detail:
    if activity_detail["heartRateDTOs"]:
        print(f"\nheartRateDTOs found: {len(activity_detail['heartRateDTOs'])} entries")
        print("First few entries:")
        for i, hr in enumerate(activity_detail["heartRateDTOs"][:5]):
            print(f"  {i}: {hr}")
    else:
        print("\nheartRateDTOs is None or empty")

if "activityDetailMetrics" in activity_detail:
    print(f"\nactivityDetailMetrics count: {len(activity_detail['activityDetailMetrics'])}")
    print("\nFirst few metrics:")
    for i, metric in enumerate(activity_detail["activityDetailMetrics"][:5]):
        print(f"  {i}: {list(metric.keys())}")
        print(f"     {metric}")
