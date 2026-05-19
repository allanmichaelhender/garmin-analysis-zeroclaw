"""Garmin-related MCP tools."""

import logging
import os
import json
from datetime import datetime, timedelta
from sqlalchemy import func, extract
from app.clients.garmin import GarminClient
from app.core.database import SessionLocal
from app.models.models import Activity, HeartRateData

logger = logging.getLogger("mcp.garmin")


def register_tools(mcp):
    """Register Garmin tools with the FastMCP instance."""

    @mcp.tool()
    def echo(message: str) -> str:
        """Echo back the input message."""
        logger.info(f"🔧 TOOL CALL: echo(message='{message}')")
        result = f"Echo: {message}"
        logger.info(f"🔧 TOOL RESULT: echo -> '{result}'")
        return result

    @mcp.tool()
    def get_hr_10sec_averages() -> str:
        """Get 10-second heart rate averages for the first workout on May 13."""
        logger.info("🔧 TOOL CALL: get_hr_10sec_averages()")

        try:
            db = SessionLocal()
            try:
                # Find the first activity on May 13 by start_time
                activity = (
                    db.query(Activity)
                    .filter(func.strftime("%m-%d", Activity.start_time) == "05-13")
                    .order_by(Activity.start_time.asc())
                    .first()
                )
            except Exception:
                activity = (
                    db.query(Activity)
                    .filter(
                        extract("month", Activity.start_time) == 5,
                        extract("day", Activity.start_time) == 13,
                    )
                    .order_by(Activity.start_time.asc())
                    .first()
                )

            if not activity:
                result = json.dumps(
                    {
                        "error": "No activity found on May 13",
                        "activity": None,
                        "hr_10sec_averages": [],
                    },
                    indent=2,
                )
                logger.info(
                    "🔧 TOOL RESULT: get_hr_10sec_averages -> no May 13 activity found"
                )
                return result

            hr_rows = (
                db.query(HeartRateData)
                .filter(HeartRateData.activity_id == activity.id)
                .order_by(HeartRateData.timestamp)
                .all()
            )

            if not hr_rows:
                result = json.dumps(
                    {
                        "error": f"No heart rate data found for activity {activity.id}",
                        "activity": {
                            "id": activity.id,
                            "type": activity.activity_type,
                            "start_time": activity.start_time.isoformat(),
                        },
                        "hr_10sec_averages": [],
                    },
                    indent=2,
                )
                logger.info(
                    f"🔧 TOOL RESULT: get_hr_10sec_averages -> no HR data for activity {activity.id}"
                )
                return result

            start_ts = hr_rows[0].timestamp
            bins = {}
            for row in hr_rows:
                elapsed = (row.timestamp - start_ts).total_seconds()
                if elapsed < 0:
                    elapsed = 0
                bin_index = int(elapsed // 10)
                bins.setdefault(bin_index, []).append(row.heart_rate)

            averages = [
                {
                    "bin_start": (
                        start_ts + timedelta(seconds=bin_index * 10)
                    ).isoformat(),
                    "avg_hr": sum(values) / len(values),
                    "samples": len(values),
                }
                for bin_index, values in sorted(bins.items())
            ]

            result_payload = {
                "activity": {
                    "id": activity.id,
                    "type": activity.activity_type,
                    "start_time": activity.start_time.isoformat(),
                    "duration_seconds": activity.duration_seconds,
                    "distance_meters": activity.distance_meters,
                },
                "hr_10sec_averages": averages,
            }

            result = json.dumps(result_payload, indent=2)
            logger.info(
                f"🔧 TOOL RESULT: get_hr_10sec_averages -> {len(averages)} averages for activity {activity.id}"
            )
            return result
        except Exception as e:
            error_msg = f"Failed to get HR 10-second averages: {str(e)}"
            logger.error(error_msg)
            return error_msg
        finally:
            try:
                db.close()
            except Exception:
                pass

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
        result = (
            f"Activity {activity_id}: running, 30min, avg HR 145bpm, pace 5.5min/km"
        )
        logger.info(f"🔧 TOOL RESULT: analyze_activity -> '{result}'")
        return result

    @mcp.tool()
    def get_recent_activities() -> str:
        """Get recent Garmin activities."""
        logger.info("🔧 TOOL CALL: get_recent_activities()")
        activities = [
            {
                "id": "1",
                "type": "running",
                "date": "2025-05-06",
                "duration_minutes": 30,
            },
            {
                "id": "2",
                "type": "cycling",
                "date": "2025-05-05",
                "duration_minutes": 45,
            },
            {
                "id": "3",
                "type": "running",
                "date": "2025-05-04",
                "duration_minutes": 25,
            },
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
                    existing = (
                        db.query(Activity).filter(Activity.id == activity_id).first()
                    )

                    activity_data = {
                        "id": activity_id,
                        "activity_type": raw_activity.get("activityType", {}).get(
                            "typeKey", "unknown"
                        ),
                        "start_time": datetime.fromisoformat(
                            raw_activity.get("startTimeLocal", "").replace(
                                "Z", "+00:00"
                            )
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
                        "avg_cadence": float(
                            raw_activity.get("averageBikingCadence", 0)
                        )
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
                        "aerobic_effect": float(
                            raw_activity.get("aerobicTrainingEffect", 0)
                        )
                        if raw_activity.get("aerobicTrainingEffect")
                        else None,
                        "anaerobic_effect": float(
                            raw_activity.get("anaerobicTrainingEffect", 0)
                        )
                        if raw_activity.get("anaerobicTrainingEffect")
                        else None,
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
