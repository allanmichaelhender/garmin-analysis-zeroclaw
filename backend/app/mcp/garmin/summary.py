"""MCP tool for activity discovery and condensed summaries.

Single get_activity_summary tool handles both modes:
  - No activity_id → returns lightweight list of recent activities
  - With activity_id → returns full condensed view with splits
"""

import json
import logging
from collections import defaultdict
from datetime import datetime

from app.core.database import SessionLocal
from app.models.models import Activity

logger = logging.getLogger("mcp.garmin.summary")


def register_tools(mcp):
    """Register summary tool with the FastMCP instance."""

    @mcp.tool()
    def get_activity_summary(
        activity_id: str | None = None,
        limit: int = 10,
        activity_type: str | None = None,
    ) -> str:
        """
        Get a condensed summary of a single activity, or list recent ones.

        - If activity_id is provided: returns full summary with key stats,
          lap/split data, and 30-second HR averages.
        - If activity_id is None: returns a lightweight list of recent
          activities so you can discover IDs to inspect.

        Args:
            activity_id: Garmin activity ID (e.g. "22866136891").
                Omit or pass None to list recent activities instead.
            limit: Max activities to return when listing (default 10).
            activity_type: Filter by type when listing (e.g. "cycling",
                "indoor_cardio", "running"). Case-insensitive.

        Returns:
            JSON — either an array of lightweight entries (when listing)
            or a single summary object with splits and HR buckets (when inspecting).
        """
        logger.info(
            f"🔧 TOOL CALL: get_activity_summary(activity_id={activity_id}, "
            f"limit={limit}, activity_type={activity_type})"
        )

        db = SessionLocal()
        try:
            # --- Mode 1: List recent activities ---
            if activity_id is None:
                query = db.query(Activity).order_by(Activity.start_time.desc())
                if activity_type:
                    query = query.filter(Activity.activity_type.ilike(activity_type))
                activities = query.limit(limit).all()

                results = []
                for a in activities:
                    results.append(
                        {
                            "id": a.id,
                            "activity_type": a.activity_type,
                            "start_time": (
                                a.start_time.isoformat() if a.start_time else None
                            ),
                            "duration_min": (
                                round(a.duration_seconds / 60, 1)
                                if a.duration_seconds
                                else None
                            ),
                            "distance_km": (
                                round(a.distance_meters / 1000, 2)
                                if a.distance_meters
                                else None
                            ),
                            "avg_heart_rate": a.avg_heart_rate,
                            "max_heart_rate": a.max_heart_rate,
                            "calories": a.calories,
                            "training_effect": a.training_effect,
                            "is_intervals": a.is_intervals,
                            "workout_structure": a.workout_structure,
                        }
                    )

                result = json.dumps(results, indent=2, default=str)
                logger.info(
                    f"🔧 TOOL RESULT: get_activity_summary (list) -> "
                    f"{len(results)} activities"
                )
                return result

            # --- Mode 2: Single activity summary ---
            activity = db.query(Activity).filter(Activity.id == activity_id).first()
            if not activity:
                error_msg = (
                    f"Activity {activity_id} not found in database. "
                    "Sync first via sync_garmin_activities."
                )
                logger.error(error_msg)
                return error_msg

            summary = {
                "id": activity.id,
                "activity_type": activity.activity_type,
                "start_time": (
                    activity.start_time.isoformat() if activity.start_time else None
                ),
                "duration_min": (
                    round(activity.duration_seconds / 60, 1)
                    if activity.duration_seconds
                    else None
                ),
                "distance_km": (
                    round(activity.distance_meters / 1000, 2)
                    if activity.distance_meters
                    else None
                ),
                "avg_heart_rate": activity.avg_heart_rate,
                "max_heart_rate": activity.max_heart_rate,
                "calories": activity.calories,
                "elevation_gain_m": activity.elevation_gain,
                "avg_power": activity.avg_power,
                "max_power": activity.max_power,
                "avg_cadence": activity.avg_cadence,
                "avg_speed_kmh": (
                    round(activity.avg_speed * 3.6, 2)
                    if activity.avg_speed is not None
                    else None
                ),
                "max_speed_kmh": (
                    round(activity.max_speed * 3.6, 2)
                    if activity.max_speed is not None
                    else None
                ),
                "training_effect": activity.training_effect,
                "aerobic_effect": activity.aerobic_effect,
                "anaerobic_effect": activity.anaerobic_effect,
                "is_intervals": activity.is_intervals,
                "workout_structure": activity.workout_structure,
                "anthropic_hr_profile": activity.anthropic_hr_profile,
            }

            summary["splits"] = _condense_splits(activity.splits_data)

            if activity.metrics_data:
                summary["hr_buckets"] = _compute_hr_buckets(activity.metrics_data)

            result = json.dumps(summary, indent=2, default=str)
            logger.info(
                f"🔧 TOOL RESULT: get_activity_summary -> {activity_id} "
                f"({len(summary['splits'])} splits"
                + (
                    f", {len(summary['hr_buckets'])} hr_buckets)"
                    if "hr_buckets" in summary
                    else ")"
                )
            )
            return result

        except Exception as e:
            error_msg = f"Error in get_activity_summary: {str(e)}"
            logger.error(error_msg)
            return error_msg
        finally:
            db.close()


def _condense_splits(splits_data: dict | None) -> list[dict]:
    """Turn raw lapDTOs from Garmin into a clean, minimal array."""
    lap_dtos = (splits_data or {}).get("lapDTOs", [])
    if not lap_dtos:
        return []

    try:
        first_start = datetime.fromisoformat(lap_dtos[0]["startTimeGMT"])
    except (KeyError, ValueError):
        return []

    results = []
    for lap in lap_dtos:
        lap_index = lap.get("lapIndex")
        if lap_index is None:
            continue

        try:
            lap_start = datetime.fromisoformat(lap["startTimeGMT"])
            rel_start = (lap_start - first_start).total_seconds()
        except (KeyError, ValueError):
            continue

        elapsed = lap.get("elapsedDuration", 0)

        results.append(
            {
                "lap_index": lap_index,
                "start_s": round(rel_start, 1),
                "end_s": round(rel_start + elapsed, 1),
                "duration_s": elapsed,
                "avg_hr": lap.get("averageHR"),
                "max_hr": lap.get("maxHR"),
                "distance_m": lap.get("distance", 0),
            }
        )

    return results


def _compute_hr_buckets(
    metrics_data: list[dict], bucket_size_s: int = 30
) -> list[dict]:
    """Average heart rate into fixed-width time buckets.

    Args:
        metrics_data: List of 1-second metric samples from the DB.
        bucket_size_s: Width of each bucket in seconds (default 30).

    Returns:
        List of {time_s, hr_avg} dicts, one per non-empty bucket.
    """
    buckets: dict[int, list[int]] = defaultdict(list)

    for entry in metrics_data:
        hr = entry.get("directHeartRate")
        elapsed = entry.get("sumElapsedDuration")
        if hr is not None and elapsed is not None and hr > 0:
            bucket = int(elapsed // bucket_size_s) * bucket_size_s
            buckets[bucket].append(int(hr))

    return [
        {"time_s": bucket, "hr_avg": round(sum(vals) / len(vals))}
        for bucket, vals in sorted(buckets.items())
    ]
