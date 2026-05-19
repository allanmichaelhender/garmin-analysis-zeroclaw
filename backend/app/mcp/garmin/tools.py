"""Garmin-related MCP tools."""

import logging
import os
from datetime import datetime
from app.clients.garmin import GarminClient
from app.core.database import SessionLocal
from app.models.models import Activity

logger = logging.getLogger("mcp.garmin")


def register_tools(mcp):
    """Register Garmin tools with the FastMCP instance."""

    @mcp.tool()
    def echo(message: str) -> str:
        """Echo back the input message for connectivity testing."""
        logger.info(f"🔧 TOOL CALL: echo(message='{message}')")
        result = f"Echo: {message}"
        logger.info(f"🔧 TOOL RESULT: echo -> '{result}'")
        return result

    @mcp.tool()
    def sync_garmin_activities(limit: int = 50) -> str:
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
                metrics_count = 0

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

                    is_new = existing is None
                    needs_metrics = is_new or (
                        existing and existing.metrics_data is None
                    )

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

                    # Fetch detailed metrics if needed (separate API call per activity)
                    if needs_metrics:
                        try:
                            detail = client.get_activity_details_with_metrics(
                                activity_id
                            )
                            if detail and detail.get("metrics"):
                                # Re-fetch the record after commit
                                record = (
                                    db.query(Activity)
                                    .filter(Activity.id == activity_id)
                                    .first()
                                )
                                if record:
                                    record.metrics_data = detail["metrics"]
                                    db.commit()
                                    metrics_count += 1
                                    logger.info(
                                        f"Saved {len(detail['metrics'])} metric samples for {activity_id}"
                                    )
                        except Exception as me:
                            logger.warning(
                                f"Failed to fetch metrics for {activity_id}: {me}"
                            )

                result = (
                    f"Synced {new_count} new, updated {updated_count} existing, "
                    f"with {metrics_count} activities having detailed metrics from Garmin"
                )
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
