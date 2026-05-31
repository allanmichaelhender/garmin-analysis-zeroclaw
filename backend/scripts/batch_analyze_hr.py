"""Batch HR profile analyzer.

Fetches the most recent N activities that don't yet have an Anthropic
HR profile, generates HR plots, and sends them to Claude for analysis.

Usage:
    python scripts/batch_analyze_hr.py [limit=10]
"""

import sys
import os
import io
import base64
import json
import logging
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.models.models import Activity
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("batch_hr")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

load_dotenv()


def analyze_activity(activity: Activity) -> str | None:
    """Run the full HR profile analysis for a single activity.

    Builds an HR plot from metrics_data, sends it with splits context
    to Anthropic Claude, saves the result to the database.

    Returns:
        The HR profile summary text, or None on failure.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY not set in environment")
        return None

    if not activity.metrics_data:
        logger.warning(f"Activity {activity.id} has no metrics_data — skipping")
        return None

    # --- Build HR plot ---
    hr_samples = []
    for entry in activity.metrics_data:
        hr = entry.get("directHeartRate")
        elapsed = entry.get("sumElapsedDuration")
        if hr is not None and hr > 0 and elapsed is not None:
            hr_samples.append((elapsed, int(hr)))

    if not hr_samples:
        logger.warning(f"Activity {activity.id} has no valid HR samples — skipping")
        return None

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

    # Save plot to disk for reference
    plot_dir = os.path.join(os.path.dirname(__file__), "..", "scripts")
    plot_path = os.path.join(plot_dir, f"hr_plot_{activity.id}.png")
    plt.savefig(plot_path, dpi=100)
    logger.info(f"Saved plot: {plot_path}")
    plt.close()

    # --- Build splits context ---
    splits = activity.splits_data or {}
    lap_dtos = splits.get("lapDTOs", [])
    if lap_dtos:
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
    db = SessionLocal()
    try:
        record = db.query(Activity).filter(Activity.id == activity.id).first()
        if record:
            record.anthropic_hr_profile = hr_profile
            db.commit()
            logger.info(f"✅ Saved HR profile for {activity.id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save HR profile for {activity.id}: {e}")
        return None
    finally:
        db.close()

    return hr_profile


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10

    db = SessionLocal()
    try:
        activities = (
            db.query(Activity)
            .filter(Activity.anthropic_hr_profile.is_(None))
            .filter(Activity.metrics_data.isnot(None))
            .order_by(Activity.start_time.desc())
            .limit(limit)
            .all()
        )
    finally:
        db.close()

    if not activities:
        logger.info("No unanalyzed activities with metrics_data found. All caught up!")
        return

    logger.info(
        f"Found {len(activities)} activities without HR profile "
        f"(limit={limit}, ordered by most recent)"
    )

    success = 0
    fail = 0
    for i, activity in enumerate(activities, 1):
        logger.info(
            f"[{i}/{len(activities)}] Analyzing {activity.id} "
            f"({activity.activity_type}, {activity.start_time})..."
        )
        result = analyze_activity(activity)
        if result:
            success += 1
        else:
            fail += 1

    logger.info(
        f"Done — {success} succeeded, {fail} failed, out of {len(activities)} attempted"
    )


if __name__ == "__main__":
    main()
