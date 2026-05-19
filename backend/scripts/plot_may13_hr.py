"""Create HR plot for the May 13th activity using metrics_data."""

import matplotlib.pyplot as plt
import sys
import os
from pathlib import Path

# Add the 'backend' directory to sys.path to enable imports like 'from app.core.database'
# when running the script from the project root or other directories.
script_dir = Path(__file__).parent
backend_dir = script_dir.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
from matplotlib.ticker import MaxNLocator
from sqlalchemy import extract, func
from app.core.database import SessionLocal
from app.models.models import Activity


def plot_may13_activity_hr():
    """Create a heart rate plot for the May 13th activity."""
    db = SessionLocal()

    try:
        # Find the first activity on May 13
        try:
            # Prefer SQLAlchemy EXTRACT for portability
            activity = (
                db.query(Activity)
                .filter(
                    extract("month", Activity.start_time) == 5,
                    extract("day", Activity.start_time) == 13,
                )
                .order_by(Activity.start_time.asc())
                .first()
            )
        except Exception:
            db.rollback()
            # Fallback to SQLite strftime
            activity = (
                db.query(Activity)
                .filter(func.strftime("%m-%d", Activity.start_time) == "05-13")
                .order_by(Activity.start_time.asc())
                .first()
            )

        if not activity:
            print("No activities found on May 13")
            return

        print(f"May 13th activity:")
        print(f"  ID: {activity.id}")
        print(f"  Type: {activity.activity_type}")
        print(f"  Date: {activity.start_time}")
        print(f"  Duration: {activity.duration_seconds / 60:.1f} minutes")

        # Get heart rate data from metrics_data JSON column
        if not activity.metrics_data:
            print("No metrics_data found in database for this activity")
            return

        # Extract HR samples using sumElapsedDuration (seconds) as x-axis
        hr_samples = []
        for entry in activity.metrics_data:
            hr = entry.get("directHeartRate")
            elapsed = entry.get("sumElapsedDuration")
            if hr is not None and hr > 0 and elapsed is not None:
                hr_samples.append((elapsed, int(hr)))

        if not hr_samples:
            print("No heart rate samples found in metrics_data")
            return

        # Print first 20 samples for debugging
        print("\n--- Heart Rate Data from metrics_data (May 13th Activity) ---")
        for i, (elapsed, hr) in enumerate(hr_samples[:20]):
            print(f"  {i + 1}: t={elapsed:.0f}s, HR={hr}")
        if len(hr_samples) > 20:
            print(f"  ... and {len(hr_samples) - 20} more samples")
        print("-----------------------------------------------------------\n")

        print(f"  HR data points: {len(hr_samples)}")

        # Extract elapsed times and heart rates
        elapsed_times = [e for e, _ in hr_samples]
        heart_rates = [hr for _, hr in hr_samples]

        # Create plot - optimized for clarity (1400x400 pixels)
        plt.figure(figsize=(14, 4), dpi=100)
        plt.plot(elapsed_times, heart_rates, color="red", linewidth=2.5)

        plt.xlabel("Elapsed Time (seconds)", fontsize=11, fontweight="bold")
        plt.ylabel("Heart Rate (BPM)", fontsize=11, fontweight="bold")
        plt.grid(True, linestyle="--", alpha=0.6, color="gray", axis="both")

        ax = plt.gca()
        ax.xaxis.set_major_locator(MaxNLocator(nbins=30))
        plt.xticks(rotation=90)
        plt.margins(x=0)
        plt.tight_layout()

        # Save plot in scripts directory
        scripts_dir = Path(__file__).parent
        output_file = str(scripts_dir / f"hr_plot_may13_{activity.id}.png")
        plt.savefig(output_file, dpi=100)
        print(f"\nPlot saved to: {output_file}")

        # Show statistics
        avg_hr = sum(heart_rates) / len(heart_rates)
        max_hr = max(heart_rates)
        min_hr = min(heart_rates)
        print(f"\nHR Statistics:")
        print(f"  Average: {avg_hr:.1f} bpm")
        print(f"  Max: {max_hr} bpm")
        print(f"  Min: {min_hr} bpm")

    finally:
        db.close()


if __name__ == "__main__":
    plot_may13_activity_hr()
