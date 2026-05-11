"""Analysis MCP tools."""

import logging
import numpy as np
from app.services.changepoint_detection import ChangepointDetector
from app.core.database import SessionLocal
from app.models.models import Activity, HeartRateData, ActivityInterval

logger = logging.getLogger("mcp.analysis")


def register_tools(mcp):
    """Register analysis tools with the FastMCP instance."""
    
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
