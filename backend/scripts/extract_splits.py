"""Extract lap/split intervals from activity splits_data.

For activity 22866136891 (May 13 indoor_cardio session):
- Reads splits_data from the database
- Extracts laps by lapIndex
- Computes relative start time (seconds from first lap)
- Prints a clean table of lapIndex, start_time, elapsed_duration, avgHR, maxHR
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add backend directory to sys.path
script_dir = Path(__file__).parent
backend_dir = script_dir.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal
from app.models.models import Activity

ACTIVITY_ID = "22866136891"


def extract_splits(activity_id: str) -> list[dict]:
    """Extract lap data from an activity's splits_data."""
    db = SessionLocal()
    try:
        activity = db.query(Activity).filter(Activity.id == activity_id).first()
        if not activity:
            print(f"Activity {activity_id} not found in database.")
            return []

        if not activity.splits_data:
            print(f"Activity {activity_id} has no splits_data.")
            return []

        lap_dtos = activity.splits_data.get("lapDTOs", [])
        if not lap_dtos:
            print(f"No lapDTOs found in splits_data for activity {activity_id}.")
            return []

        # Parse first lap start time as reference point (t=0)
        first_lap_start = datetime.fromisoformat(lap_dtos[0]["startTimeGMT"])
        results = []

        for lap in lap_dtos:
            lap_index = lap.get("lapIndex")
            if lap_index is None:
                # Skip laps without an assigned lap index
                continue

            lap_start = datetime.fromisoformat(lap["startTimeGMT"])
            relative_start = (lap_start - first_lap_start).total_seconds()

            elapsed = lap.get("elapsedDuration", 0)
            end_time = round(relative_start + elapsed, 1)

            results.append(
                {
                    "lap_index": lap_index,
                    "start_time_relative_s": round(relative_start, 1),
                    "end_time_relative_s": end_time,
                    "start_time_abs": lap["startTimeGMT"],
                    "elapsed_duration_s": elapsed,
                    "avg_hr": lap.get("averageHR"),
                    "max_hr": lap.get("maxHR"),
                }
            )

        return results

    finally:
        db.close()


def print_results(results: list[dict]):
    """Print extracted lap data as a formatted table."""
    if not results:
        return

    print(f"\n=== Activity {ACTIVITY_ID} — Lap Intervals ===")
    print(
        f"{'Lap':<6} {'Start (rel, s)':<16} {'End (rel, s)':<14} {'Duration (s)':<14} {'Avg HR':<8} {'Max HR':<8}"
    )
    print("-" * 66)

    for r in results:
        print(
            f"{r['lap_index']:<6} {r['start_time_relative_s']:<16.1f} "
            f"{r['end_time_relative_s']:<14.1f} "
            f"{r['elapsed_duration_s']:<14.1f} {r['avg_hr']:<8} {r['max_hr']:<8}"
        )

    print("-" * 66)
    total_duration = sum(r["elapsed_duration_s"] for r in results)
    print(f"\nTotal laps: {len(results)}")
    print(f"Total elapsed: {total_duration:.1f}s ({total_duration / 60:.1f} min)")


if __name__ == "__main__":
    results = extract_splits(ACTIVITY_ID)
    print_results(results)
