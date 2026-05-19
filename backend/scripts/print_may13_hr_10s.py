"""Print 10-second average heart rate for the first activity on May 13."""

from __future__ import annotations
import os
import sys
from datetime import timedelta

# Ensure backend package is importable when running from repo root
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from dotenv import load_dotenv
from sqlalchemy import func, extract

from app.core.database import SessionLocal
from app.models.models import Activity, HeartRateData

load_dotenv()


def find_first_may13_activity(db):
    """Find the first activity on May 13 (any year)."""
    query = (
        db.query(Activity)
        .filter(
            extract("month", Activity.start_time) == 5,
            extract("day", Activity.start_time) == 13,
        )
        .order_by(Activity.start_time.asc())
    )

    try:
        return query.first()
    except Exception:
        # Fallback for SQLite if extract() is unavailable
        return (
            db.query(Activity)
            .filter(func.strftime("%m-%d", Activity.start_time) == "05-13")
            .order_by(Activity.start_time.asc())
            .first()
        )


def compute_10s_averages(hr_data):
    """Compute 10-second average HR bins from ordered HeartRateData rows."""
    if not hr_data:
        return []

    start_ts = hr_data[0].timestamp
    bins = {}

    for row in hr_data:
        elapsed_seconds = (row.timestamp - start_ts).total_seconds()
        if elapsed_seconds < 0:
            elapsed_seconds = 0
        bin_index = int(elapsed_seconds // 10)
        bins.setdefault(bin_index, []).append(row.heart_rate)

    averages = []
    for bin_index in sorted(bins):
        values = bins[bin_index]
        avg_hr = sum(values) / len(values)
        bin_start = start_ts + timedelta(seconds=bin_index * 10)
        averages.append((bin_start, avg_hr, len(values)))

    return averages


def main():
    db = SessionLocal()
    try:
        activity = find_first_may13_activity(db)
        if not activity:
            print("No activity found on May 13.")
            return

        print("First activity on May 13:")
        print(f"  ID: {activity.id}")
        print(f"  Type: {activity.activity_type}")
        print(f"  Start: {activity.start_time}")
        print(f"  Duration: {activity.duration_seconds or 0} seconds")
        print()

        hr_rows = (
            db.query(HeartRateData)
            .filter(HeartRateData.activity_id == activity.id)
            .order_by(HeartRateData.timestamp)
            .all()
        )

        if not hr_rows:
            print("No heart rate data found for this activity.")
            return

        averages = compute_10s_averages(hr_rows)
        if not averages:
            print("No 10-second HR averages could be computed.")
            return

        print("10-second average heart rate:")
        for timestamp, avg_hr, count in averages:
            print(f"{timestamp}  avg_hr={avg_hr:.1f} bpm  samples={count}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
