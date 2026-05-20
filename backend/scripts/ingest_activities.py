"""Ingest Garmin activities from Garmin Connect API."""

import sys
import os
import logging
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.clients.garmin import GarminClient
from app.core.database import SessionLocal, init_db
from app.models.models import Activity
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def parse_activity_data(raw_activity: dict) -> dict:
    """
    Parse raw Garmin activity data into database format.

    Args:
        raw_activity: Raw activity data from Garmin API

    Returns:
        Parsed activity dictionary
    """
    return {
        "id": str(raw_activity.get("activityId", "")),
        "activity_type": raw_activity.get("activityType", {}).get("typeKey", "unknown"),
        "start_time": datetime.fromisoformat(
            raw_activity.get("startTimeLocal", "").replace("Z", "+00:00")
        )
        if raw_activity.get("startTimeLocal")
        else None,
        "duration_seconds": int(raw_activity.get("duration", 0)),
        "distance_meters": float(raw_activity.get("distance", 0)),
        "avg_heart_rate": int(raw_activity.get("averageHR", 0))
        if raw_activity.get("averageHR")
        else None,
        "max_heart_rate": int(raw_activity.get("maxHR", 0))
        if raw_activity.get("maxHR")
        else None,
        "calories": int(raw_activity.get("calories", 0)),
        "avg_speed": float(raw_activity.get("averageSpeed", 0))
        if raw_activity.get("averageSpeed")
        else None,
        "max_speed": float(raw_activity.get("maxSpeed", 0))
        if raw_activity.get("maxSpeed")
        else None,
        "elevation_gain": float(raw_activity.get("elevationGain", 0))
        if raw_activity.get("elevationGain")
        else None,
        "elevation_loss": float(raw_activity.get("elevationLoss", 0))
        if raw_activity.get("elevationLoss")
        else None,
        "avg_cadence": float(raw_activity.get("averageBikingCadence", 0))
        if raw_activity.get("averageBikingCadence")
        else None,
        "max_cadence": float(raw_activity.get("maxBikingCadence", 0))
        if raw_activity.get("maxBikingCadence")
        else None,
        "avg_power": float(raw_activity.get("averageWatts", 0))
        if raw_activity.get("averageWatts")
        else None,
        "max_power": float(raw_activity.get("maxWatts", 0))
        if raw_activity.get("maxWatts")
        else None,
        "training_effect": float(raw_activity.get("trainingEffect", 0))
        if raw_activity.get("trainingEffect")
        else None,
        "aerobic_effect": float(raw_activity.get("aerobicTrainingEffect", 0))
        if raw_activity.get("aerobicTrainingEffect")
        else None,
        "anaerobic_effect": float(raw_activity.get("anaerobicTrainingEffect", 0))
        if raw_activity.get("anaerobicTrainingEffect")
        else None,
        "raw_data": raw_activity,
    }


def ingest_activities(limit: int = 50):
    """
    Ingest activities from Garmin Connect to database.

    Args:
        limit: Maximum number of activities to ingest
    """
    # Get credentials from environment
    email = os.getenv("GARMIN_EMAIL")
    password = os.getenv("GARMIN_PASSWORD")

    if not email or not password:
        logger.error("GARMIN_EMAIL and GARMIN_PASSWORD must be set in .env file")
        return

    # Initialize database
    init_db()

    # Create Garmin client
    client = GarminClient(email, password)

    # Authenticate
    if not client.authenticate():
        logger.error("Failed to authenticate with Garmin Connect")
        return

    # Fetch activities
    logger.info(f"Fetching last {limit} activities from Garmin...")
    activities = client.get_activities(limit=limit)

    if not activities:
        logger.warning("No activities found")
        return

    # Store in database
    db = SessionLocal()
    try:
        ingested_count = 0
        updated_count = 0
        metrics_count = 0
        splits_count = 0

        for raw_activity in activities:
            activity_id = str(raw_activity.get("activityId", ""))

            # Check if activity already exists
            existing = db.query(Activity).filter(Activity.id == activity_id).first()

            # Parse activity data
            activity_data = parse_activity_data(raw_activity)

            if existing:
                # Update existing activity using merge
                for key, value in activity_data.items():
                    setattr(existing, key, value)
                db.add(existing)
                updated_count += 1
                logger.info(f"Updated activity {activity_id}")
            else:
                # Create new activity
                activity = Activity(**activity_data)
                db.add(activity)
                ingested_count += 1
                logger.info(
                    f"Ingested activity {activity_id} - {activity_data['activity_type']}"
                )

            # Commit each activity individually to avoid parameter conflicts
            db.commit()
            db.expunge_all()  # Clear session to avoid parameter conflicts

            # Fetch splits data (separate API call per activity)
            try:
                splits = client.get_activity_splits(activity_id)
                if splits:
                    record = (
                        db.query(Activity).filter(Activity.id == activity_id).first()
                    )
                    if record:
                        record.splits_data = splits
                        db.commit()
                        splits_count += 1
                        logger.info(f"Saved splits data for activity {activity_id}")
            except Exception as se:
                logger.warning(f"Failed to fetch splits for {activity_id}: {se}")

        logger.info(
            f"Successfully ingested {ingested_count} new activities, "
            f"updated {updated_count} existing activities, "
            f"with {splits_count} activities having splits data"
        )

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to ingest activities: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    ingest_activities(limit=limit)
