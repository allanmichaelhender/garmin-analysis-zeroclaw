"""FastMCP tool definitions for Garmin data access."""

import logging
import os
from datetime import datetime, timedelta
import json
from fastmcp import FastMCP
from app.services.changepoint_detection import ChangepointDetector
from app.clients.garmin import GarminClient
from app.core.database import SessionLocal
from app.models.models import Activity, HeartRateData, ActivityInterval, WorkoutMetadata
import numpy as np
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mcp_tools")

# Load environment variables
load_dotenv()

# Create FastMCP instance
mcp = FastMCP("garmin-mcp-server")
http_app = mcp.http_app(path="/", transport="http")
sse_app = mcp.http_app(path="/", transport="sse")


@mcp.tool()
def echo(message: str) -> str:
    """Echo back the input message."""
    logger.info(f"🔧 TOOL CALL: echo(message='{message}')")
    result = f"Echo: {message}"
    logger.info(f"🔧 TOOL RESULT: echo -> '{result}'")
    return result


@mcp.tool()
def get_garmin_data(date: str = "today") -> str:
    """Get Garmin activity data for a specific date."""
    logger.info(f"🔧 TOOL CALL: get_garmin_data(date='{date}')")
    result = f"Garmin data for {date}: steps=10000, calories=500, distance=5.2km"
    logger.info(f"🔧 TOOL RESULT: get_garmin_data -> '{result}'")
    return result


@mcp.tool()
def analyze_activity(activity_id: str) -> str:
    """Analyze a Garmin activity by ID."""
    logger.info(f"🔧 TOOL CALL: analyze_activity(activity_id='{activity_id}')")
    result = f"Activity {activity_id}: running, 30min, avg HR 145bpm, pace 5.5min/km"
    logger.info(f"🔧 TOOL RESULT: analyze_activity -> '{result}'")
    return result


@mcp.tool()
def get_recent_activities() -> str:
    """Get recent Garmin activities."""
    logger.info("🔧 TOOL CALL: get_recent_activities()")
    activities = [
        {"id": "1", "type": "running", "date": "2025-05-06", "duration_minutes": 30},
        {"id": "2", "type": "cycling", "date": "2025-05-05", "duration_minutes": 45},
        {"id": "3", "type": "running", "date": "2025-05-04", "duration_minutes": 25},
    ]
    result = f"Recent activities: {activities}"
    logger.info(f"🔧 TOOL RESULT: get_recent_activities -> '{result}'")
    return result


@mcp.tool()
def sync_garmin_activities(limit: int = 20) -> str:
    """
    Sync new activities from Garmin Connect to the database.

    Args:
        limit: Maximum number of recent activities to sync

    Returns:
        Summary of synced activities
    """
    logger.info(f"🔧 TOOL CALL: sync_garmin_activities(limit={limit})")

    email = os.getenv("GARMIN_EMAIL")
    password = os.getenv("GARMIN_PASSWORD")

    if not email or not password:
        error_msg = "GARMIN_EMAIL and GARMIN_PASSWORD must be set in environment"
        logger.error(error_msg)
        return error_msg

    try:
        client = GarminClient(email, password)
        if not client.authenticate():
            error_msg = "Failed to authenticate with Garmin Connect"
            logger.error(error_msg)
            return error_msg

        activities = client.get_activities(limit=limit)
        if not activities:
            result = "No activities found on Garmin"
            logger.info(f"🔧 TOOL RESULT: sync_garmin_activities -> '{result}'")
            return result

        db = SessionLocal()
        try:
            new_count = 0
            updated_count = 0

            for raw_activity in activities:
                activity_id = str(raw_activity.get("activityId", ""))
                existing = db.query(Activity).filter(Activity.id == activity_id).first()

                activity_data = {
                    "id": activity_id,
                    "activity_type": raw_activity.get("activityType", {}).get("typeKey", "unknown"),
                    "start_time": datetime.fromisoformat(raw_activity.get("startTimeLocal", "").replace("Z", "+00:00")) if raw_activity.get("startTimeLocal") else None,
                    "duration_seconds": int(raw_activity.get("duration", 0)),
                    "distance_meters": float(raw_activity.get("distance", 0)),
                    "avg_heart_rate": int(raw_activity.get("averageHR", 0)) if raw_activity.get("averageHR") else None,
                    "max_heart_rate": int(raw_activity.get("maxHR", 0)) if raw_activity.get("maxHR") else None,
                    "calories": int(raw_activity.get("calories", 0)),
                    "avg_speed": float(raw_activity.get("averageSpeed", 0)) if raw_activity.get("averageSpeed") else None,
                    "max_speed": float(raw_activity.get("maxSpeed", 0)) if raw_activity.get("maxSpeed") else None,
                    "elevation_gain": float(raw_activity.get("elevationGain", 0)) if raw_activity.get("elevationGain") else None,
                    "elevation_loss": float(raw_activity.get("elevationLoss", 0)) if raw_activity.get("elevationLoss") else None,
                    "avg_cadence": float(raw_activity.get("averageBikingCadence", 0)) if raw_activity.get("averageBikingCadence") else None,
                    "max_cadence": float(raw_activity.get("maxBikingCadence", 0)) if raw_activity.get("maxBikingCadence") else None,
                    "avg_power": float(raw_activity.get("averageWatts", 0)) if raw_activity.get("averageWatts") else None,
                    "max_power": float(raw_activity.get("maxWatts", 0)) if raw_activity.get("maxWatts") else None,
                    "training_effect": float(raw_activity.get("trainingEffect", 0)) if raw_activity.get("trainingEffect") else None,
                    "aerobic_effect": float(raw_activity.get("aerobicTrainingEffect", 0)) if raw_activity.get("aerobicTrainingEffect") else None,
                    "anaerobic_effect": float(raw_activity.get("anaerobicTrainingEffect", 0)) if raw_activity.get("anaerobicTrainingEffect") else None,
                    "raw_data": raw_activity,
                }

                if existing:
                    for key, value in activity_data.items():
                        setattr(existing, key, value)
                    db.add(existing)
                    updated_count += 1
                else:
                    activity = Activity(**activity_data)
                    db.add(activity)
                    new_count += 1

                db.commit()
                db.expunge_all()

            result = f"Synced {new_count} new activities, updated {updated_count} existing activities from Garmin"
            logger.info(f"🔧 TOOL RESULT: sync_garmin_activities -> '{result}'")
            return result

        except Exception as e:
            db.rollback()
            error_msg = f"Database error: {str(e)}"
            logger.error(error_msg)
            return error_msg
        finally:
            db.close()

    except Exception as e:
        error_msg = f"Failed to sync activities: {str(e)}"
        logger.error(error_msg)
        return error_msg


@mcp.tool()
def get_pending_metadata(days: int = 7) -> str:
    """
    Get activities that don't have workout metadata (RPE, session structure, notes).

    Args:
        days: Only look at activities from the last N days

    Returns:
        List of activities needing metadata
    """
    logger.info(f"🔧 TOOL CALL: get_pending_metadata(days={days})")

    db = SessionLocal()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Get activities without metadata
        activities = db.query(Activity).filter(
            Activity.start_time >= cutoff_date
        ).order_by(Activity.start_time.desc()).all()

        pending = []
        for activity in activities:
            metadata = db.query(WorkoutMetadata).filter(
                WorkoutMetadata.activity_id == activity.id
            ).first()
            if not metadata:
                pending.append({
                    "id": activity.id,
                    "type": activity.activity_type,
                    "date": activity.start_time.strftime("%Y-%m-%d %H:%M"),
                    "duration_min": round(activity.duration_seconds / 60, 1) if activity.duration_seconds else None,
                    "distance_km": round(activity.distance_meters / 1000, 2) if activity.distance_meters else None,
                })

        if not pending:
            result = f"No activities from the last {days} days need metadata"
            logger.info(f"🔧 TOOL RESULT: get_pending_metadata -> '{result}'")
            return result

        summary_parts = [f"Found {len(pending)} activities needing metadata:"]
        for idx, act in enumerate(pending[:10], 1):
            summary_parts.append(
                f"{idx}. {act['type']} on {act['date']} (ID: {act['id']})"
            )
            if act['duration_min']:
                summary_parts.append(f"   Duration: {act['duration_min']} min")
            if act['distance_km']:
                summary_parts.append(f"   Distance: {act['distance_km']} km")

        if len(pending) > 10:
            summary_parts.append(f"... and {len(pending) - 10} more")

        result = "\n".join(summary_parts)
        logger.info(f"🔧 TOOL RESULT: get_pending_metadata -> '{result}'")
        return result

    except Exception as e:
        error_msg = f"Failed to get pending metadata: {str(e)}"
        logger.error(error_msg)
        return error_msg
    finally:
        db.close()


@mcp.tool()
def save_workout_metadata(
    activity_id: str,
    rpe: int = None,
    feeling: str = None,
    session_structure: str = None,
    focus_areas: str = None,
    notes: str = None
) -> str:
    """
    Save workout metadata for an activity.

    Args:
        activity_id: Garmin activity ID
        rpe: Rate of Perceived Exertion (1-10)
        feeling: How the workout felt (great, good, okay, bad, terrible)
        session_structure: Session structure description (e.g., "warmup, 5x1km intervals, cooldown")
        focus_areas: Focus areas (e.g., "endurance, speed")
        notes: Free-form notes about the workout

    Returns:
        Confirmation of saved metadata
    """
    logger.info(f"🔧 TOOL CALL: save_workout_metadata(activity_id='{activity_id}', rpe={rpe}, feeling='{feeling}')")

    db = SessionLocal()
    try:
        # Check if activity exists
        activity = db.query(Activity).filter(Activity.id == activity_id).first()
        if not activity:
            error_msg = f"Activity {activity_id} not found in database"
            logger.info(f"🔧 TOOL RESULT: save_workout_metadata -> '{error_msg}'")
            return error_msg

        # Parse JSON fields
        structure_json = json.loads(session_structure) if session_structure else None
        focus_json = json.loads(focus_areas) if focus_areas else None

        # Check if metadata already exists
        metadata = db.query(WorkoutMetadata).filter(
            WorkoutMetadata.activity_id == activity_id
        ).first()

        if metadata:
            # Update existing
            if rpe is not None:
                metadata.rpe = rpe
            if feeling is not None:
                metadata.feeling = feeling
            if structure_json is not None:
                metadata.session_structure = structure_json
            if focus_json is not None:
                metadata.focus_areas = focus_json
            if notes is not None:
                metadata.notes = notes
            metadata.updated_at = datetime.utcnow()
            result = f"Updated metadata for activity {activity_id}"
        else:
            # Create new
            metadata = WorkoutMetadata(
                activity_id=activity_id,
                rpe=rpe,
                feeling=feeling,
                session_structure=structure_json,
                focus_areas=focus_json,
                notes=notes
            )
            db.add(metadata)
            result = f"Saved metadata for activity {activity_id}"

        db.commit()
        logger.info(f"🔧 TOOL RESULT: save_workout_metadata -> '{result}'")
        return result

    except Exception as e:
        db.rollback()
        error_msg = f"Failed to save metadata: {str(e)}"
        logger.error(error_msg)
        return error_msg
    finally:
        db.close()


@mcp.tool()
def detect_activity_intervals(activity_id: str, penalty: float = 50.0, model: str = "rbf") -> str:
    """
    Detect intervals in a workout using changepoint detection.

    Args:
        activity_id: Garmin activity ID
        penalty: Sensitivity parameter (higher = fewer intervals)
        model: Detection model ('rbf', 'linear', 'normal')

    Returns:
        Summary of detected intervals
    """
    logger.info(f"🔧 TOOL CALL: detect_activity_intervals(activity_id='{activity_id}', penalty={penalty}, model='{model}')")

    db = SessionLocal()
    try:
        # Fetch activity from database
        activity = db.query(Activity).filter(Activity.id == activity_id).first()
        if not activity:
            result = f"Activity {activity_id} not found in database"
            logger.info(f"🔧 TOOL RESULT: detect_activity_intervals -> '{result}'")
            return result

        # Extract heart rate from database
        heart_rate_samples = []
        
        # Try to get heart rate from HeartRateData table
        hr_data = db.query(HeartRateData).filter(
            HeartRateData.activity_id == activity_id
        ).order_by(HeartRateData.timestamp).all()
        
        if hr_data:
            heart_rate_samples = [hr.heart_rate for hr in hr_data]
            logger.info(f"Found {len(heart_rate_samples)} heart rate samples in database")
        else:
            logger.warning(f"No heart rate data found in database for activity {activity_id}")
            return f"No heart rate data found in database for activity {activity_id}. Please run heart rate data ingestion first."

        # Convert to numpy array
        signal = np.array(heart_rate_samples)

        # Run changepoint detection
        detector = ChangepointDetector(penalty=penalty, model=model)
        intervals = detector.detect_intervals(signal)

        if not intervals:
            result = f"No intervals detected for activity {activity_id}"
            logger.info(f"🔧 TOOL RESULT: detect_activity_intervals -> '{result}'")
            return result

        # Store intervals in database
        # First, delete existing intervals for this activity
        db.query(ActivityInterval).filter(ActivityInterval.activity_id == activity_id).delete()

        # Add new intervals
        for idx, interval_data in enumerate(intervals):
            interval = ActivityInterval(
                activity_id=activity_id,
                interval_index=idx,
                start_idx=interval_data["start_idx"],
                end_idx=interval_data["end_idx"],
                duration_samples=interval_data["duration_samples"],
                hr_mean=interval_data["mean"],
                hr_std=interval_data["std"],
                hr_min=int(interval_data["min"]),
                hr_max=int(interval_data["max"]),
                hr_median=interval_data["median"],
                penalty=penalty,
                model=model
            )
            db.add(interval)

        db.commit()

        # Build summary
        summary_parts = [
            f"Activity {activity_id} ({activity.activity_type})",
            f"Detected {len(intervals)} intervals with penalty={penalty}",
        ]

        for idx, interval in enumerate(intervals[:5]):  # Show first 5 intervals
            summary_parts.append(
                f"  Interval {idx + 1}: {interval['duration_samples']} samples, "
                f"HR {int(interval['min'])}-{int(interval['max'])}bpm (avg {int(interval['mean'])}bpm)"
            )

        if len(intervals) > 5:
            summary_parts.append(f"  ... and {len(intervals) - 5} more intervals")

        result = "\n".join(summary_parts)
        logger.info(f"🔧 TOOL RESULT: detect_activity_intervals -> '{result}'")
        return result

    except Exception as e:
        db.rollback()
        error_msg = f"Failed to detect intervals: {str(e)}"
        logger.error(error_msg)
        return error_msg
    finally:
        db.close()
