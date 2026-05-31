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
                metrics_count = 0
                splits_count = 0

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

                    # Fetch splits data (separate API call per activity)
                    try:
                        splits = client.get_activity_splits(activity_id)
                        if splits:
                            record = (
                                db.query(Activity)
                                .filter(Activity.id == activity_id)
                                .first()
                            )
                            if record:
                                record.splits_data = splits
                                db.commit()
                                splits_count += 1
                                logger.info(
                                    f"Saved splits data for activity {activity_id}"
                                )
                    except Exception as se:
                        logger.warning(
                            f"Failed to fetch splits for {activity_id}: {se}"
                        )

                result = (
                    f"Synced {new_count} new, updated {updated_count} existing, "
                    f"with {metrics_count} activities having detailed metrics "
                    f"and {splits_count} activities having splits data from Garmin"
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

    @mcp.tool()
    def update_workout_metadata(
        activity_id: str,
        is_intervals: str,
        workout_structure: str,
    ) -> str:
        """
        Record workout classification metadata for an activity.

        Call this after syncing to label whether the workout was
        interval-based and describe its structure.

        Args:
            activity_id: Garmin activity ID
            is_intervals: "true" if interval workout, "false" if steady state
            workout_structure: Description of the workout structure (e.g.
                "5 x 3min threshold / 2min rest")

        Returns:
            Confirmation message
        """
        logger.info(
            f"🔧 TOOL CALL: update_workout_metadata(activity_id={activity_id}, "
            f"is_intervals={is_intervals}, "
            f"workout_structure='{workout_structure}')"
        )

        db = SessionLocal()
        try:
            activity = db.query(Activity).filter(Activity.id == activity_id).first()
            if not activity:
                error_msg = f"Activity {activity_id} not found in database"
                logger.error(error_msg)
                return error_msg

            activity.is_intervals = is_intervals
            activity.workout_structure = workout_structure
            db.commit()

            result = (
                f"Metadata saved for activity {activity_id}: "
                f"intervals={is_intervals}, "
                f"structure='{workout_structure}'"
            )
            logger.info(f"🔧 TOOL RESULT: update_workout_metadata -> '{result}'")
            return result

        except Exception as e:
            db.rollback()
            error_msg = f"Database error: {str(e)}"
            logger.error(error_msg)
            return error_msg
        finally:
            db.close()

    @mcp.tool()
    def analyze_hr_profile(activity_id: str = "22866136891") -> str:
        """
        Generate an HR profile analysis for an activity using Anthropic.

        Creates an HR plot from metrics_data, sends it along with splits
        and workout structure to Anthropic for analysis, and stores the
        result in the database.

        Args:
            activity_id: Garmin activity ID (default: 22866136891)

        Returns:
            HR profile summary, splits data, and workout structure
        """
        logger.info(f"🔧 TOOL CALL: analyze_hr_profile(activity_id={activity_id})")

        import io
        import base64
        import json
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.ticker import MaxNLocator

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            error_msg = "ANTHROPIC_API_KEY must be set in environment"
            logger.error(error_msg)
            return error_msg

        db = SessionLocal()
        try:
            activity = db.query(Activity).filter(Activity.id == activity_id).first()
            if not activity:
                error_msg = f"Activity {activity_id} not found"
                logger.error(error_msg)
                return error_msg

            if not activity.metrics_data:
                error_msg = f"No metrics_data for activity {activity_id}"
                logger.error(error_msg)
                return error_msg

            # --- Build HR plot in memory ---
            hr_samples = []
            for entry in activity.metrics_data:
                hr = entry.get("directHeartRate")
                elapsed = entry.get("sumElapsedDuration")
                if hr is not None and hr > 0 and elapsed is not None:
                    hr_samples.append((elapsed, int(hr)))

            if not hr_samples:
                error_msg = f"No HR samples found for activity {activity_id}"
                logger.error(error_msg)
                return error_msg

            elapsed_times = [e for e, _ in hr_samples]
            heart_rates = [hr for _, hr in hr_samples]

            plt.figure(figsize=(14, 4), dpi=100)
            plt.plot(elapsed_times, heart_rates, color="red", linewidth=2.5)
            plt.xlabel("Elapsed Time (seconds)", fontsize=11, fontweight="bold")
            plt.ylabel("Heart Rate (BPM)", fontsize=11, fontweight="bold")
            plt.grid(True, linestyle="--", alpha=0.6, color="gray", axis="both")
            ax = plt.gca()
            ax.xaxis.set_major_locator(MaxNLocator(nbins=55))
            plt.xticks(rotation=90)
            plt.margins(x=0)
            plt.tight_layout()

            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=100)
            buf.seek(0)
            img_b64 = base64.b64encode(buf.read()).decode("utf-8")

            # Also save to disk so user can see what the LLM sees
            plot_path = f"/app/scripts/hr_plot_{activity_id}.png"
            plt.savefig(plot_path, dpi=100)
            logger.info(f"Saved HR plot to {plot_path}")

            plt.close()

            # --- Build prompt context ---
            splits = activity.splits_data or {}
            lap_dtos = splits.get("lapDTOs", [])
            if lap_dtos:
                # Build condensed splits summary
                first_start = datetime.fromisoformat(lap_dtos[0]["startTimeGMT"])
                lines = []
                for lap in lap_dtos:
                    lap_idx = lap.get("lapIndex", "?")
                    lap_start = datetime.fromisoformat(lap["startTimeGMT"])
                    rel_start = (lap_start - first_start).total_seconds()
                    elapsed = lap.get("elapsedDuration", 0)
                    rel_end = rel_start + elapsed
                    avg_hr = lap.get("averageHR", "?")
                    max_hr = lap.get("maxHR", "?")
                    lines.append(
                        f"Lap {lap_idx}: {rel_start:.0f}s-{rel_end:.0f}s "
                        f"({elapsed:.0f}s)  HR avg={avg_hr}  max={max_hr}"
                    )
                splits_summary = "\n".join(lines)
            else:
                splits_summary = "No splits data"

            structure = activity.workout_structure or "Not specified"

            # --- Call Anthropic ---
            from anthropic import Anthropic

            client = Anthropic(api_key=api_key)
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2000,
                cache_control={"type": "ephemeral"},
                system=[
                    {
                        "type": "text",
                        "text": (
                            "You are an expert exercise physiologist analyzing a heart rate plot. "
                            "Given the HR plot, workout structure, and splits data, provide a "
                            "concise summary of the HR profile over the course of the workout. "
                            "Describe trends, zones, recovery patterns, and how the HR response "
                            "lines up with each specific workout element. "
                            "Refer to the workout elements by name and explain "
                            "how the heart rate behaves during each one."
                        ),
                    }
                ],
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": img_b64,
                                },
                            },
                            {
                                "type": "text",
                                "text": (
                                    f"Workout structure: {structure}\n\n"
                                    f"Splits/lap data:\n{splits_summary}"
                                ),
                            },
                        ],
                    }
                ],
            )

            hr_profile = response.content[0].text

            # --- Save to DB ---
            activity.anthropic_hr_profile = hr_profile
            db.commit()

            # --- Return structured result ---
            result = json.dumps(
                {
                    "hr_profile_summary": hr_profile,
                    "splits_summary": splits_summary,
                    "workout_structure": structure,
                },
                indent=2,
            )
            logger.info(
                f"🔧 TOOL RESULT: analyze_hr_profile -> saved for {activity_id}"
            )
            return result

        except Exception as e:
            db.rollback()
            error_msg = f"Analysis error: {str(e)}"
            logger.error(error_msg)
            return error_msg
        finally:
            db.close()
