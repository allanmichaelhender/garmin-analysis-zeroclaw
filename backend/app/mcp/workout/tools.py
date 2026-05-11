"""Workout metadata MCP tools."""

import logging
import json
from datetime import datetime, timedelta
from app.core.database import SessionLocal
from app.models.models import Activity, WorkoutMetadata

logger = logging.getLogger("mcp.workout")


def register_tools(mcp):
    """Register workout metadata tools with the FastMCP instance."""
    
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
