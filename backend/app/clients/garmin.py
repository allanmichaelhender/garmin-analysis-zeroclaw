"""Garmin Connect API client for fetching activity data."""

import logging
from garminconnect import Garmin

logger = logging.getLogger(__name__)


class GarminClient:
    """Client for interacting with Garmin Connect API."""

    def __init__(self, email: str, password: str):
        """
        Initialize Garmin client with credentials.

        Args:
            email: Garmin Connect email
            password: Garmin Connect password
        """
        self.email = email
        self.password = password
        self.client = Garmin(email, password)
        self._authenticated = False

    def authenticate(self) -> bool:
        """
        Authenticate with Garmin Connect.

        Returns:
            True if authentication successful, False otherwise
        """
        try:
            self.client.login()
            self._authenticated = True
            logger.info(f"Successfully authenticated as {self.email}")
            return True
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False

    def get_activities(self, limit: int = 50) -> list[dict]:
        """
        Fetch recent activities from Garmin.

        Args:
            limit: Maximum number of activities to fetch

        Returns:
            List of activity dictionaries
        """
        if not self._authenticated:
            if not self.authenticate():
                return []

        try:
            all_activities = []
            start = 0
            batch_size = 20  # Garmin API typically returns 20 per request

            while len(all_activities) < limit:
                activities = self.client.get_activities(start, start + batch_size)
                if not activities:
                    break

                all_activities.extend(activities)
                start += batch_size

                # If we got fewer than expected, we've reached the end
                if len(activities) < batch_size:
                    break

            # Trim to requested limit
            all_activities = all_activities[:limit]
            logger.info(f"Fetched {len(all_activities)} activities from Garmin")
            return all_activities
        except Exception as e:
            logger.error(f"Failed to fetch activities: {e}")
            return []

    def get_activity(self, activity_id: str) -> dict:
        """
        Fetch the summary for a single activity by ID.

        Args:
            activity_id: Garmin activity ID

        Returns:
            Activity summary dictionary
        """
        if not self._authenticated:
            if not self.authenticate():
                return {}

        try:
            summary = self.client.get_activity(activity_id)
            logger.info(f"Fetched summary for activity {activity_id}")
            return summary
        except Exception as e:
            logger.error(f"Failed to fetch activity {activity_id}: {e}")
            return {}

    def get_activity_details(self, activity_id: str) -> dict:
        """
        Fetch detailed information for a specific activity.

        Args:
            activity_id: Garmin activity ID

        Returns:
            Activity details dictionary
        """
        if not self._authenticated:
            if not self.authenticate():
                return {}

        try:
            details = self.client.get_activity_details(activity_id)
            logger.info(f"Fetched details for activity {activity_id}")
            return details
        except Exception as e:
            logger.error(f"Failed to fetch activity details: {e}")
            return {}

    def get_activity_splits(self, activity_id: str) -> dict | None:
        """
        Fetch split/interval data for a specific activity.

        Splits represent laps or intervals within an activity, including
        metrics like distance, duration, pace, heart rate, cadence, etc.

        Args:
            activity_id: Garmin activity ID

        Returns:
            Dict with split data from Garmin API, or None if unavailable
        """
        if not self._authenticated:
            if not self.authenticate():
                return None

        try:
            splits = self.client.get_activity_splits(activity_id)
            logger.info(f"Fetched splits for activity {activity_id}")
            return splits
        except Exception as e:
            logger.error(f"Failed to fetch activity splits: {e}")
            return None

    def get_activity_details_with_metrics(self, activity_id: str) -> dict | None:
        """
        Fetch detailed activity data including 1-second metrics and return
        structured data ready for storage.

        Args:
            activity_id: Garmin activity ID

        Returns:
            Dict with 'activity_details' (raw API response) and 'metrics' (structured array),
            or None if unavailable
        """
        if not self._authenticated:
            if not self.authenticate():
                return None

        try:
            details = self.client.get_activity_details(activity_id)
            if not details:
                logger.warning(f"No details returned for activity {activity_id}")
                return None

            result = {
                "activity_details": details,
                "metrics": [],
            }

            if (
                "activityDetailMetrics" not in details
                or "metricDescriptors" not in details
            ):
                logger.warning(
                    f"No metricDescriptors/activityDetailMetrics for {activity_id}"
                )
                return result

            # Build metric key → index mapping
            key_index = {}
            for desc in details["metricDescriptors"]:
                key = desc.get("key")
                idx = desc.get("metricsIndex")
                if key is not None and idx is not None:
                    key_index[key] = idx

            logger.info(f"Metric keys for {activity_id}: {list(key_index.keys())}")

            # Extract metric values with timestamps
            for entry in details["activityDetailMetrics"]:
                if "metrics" not in entry:
                    continue

                sample = {}
                if "startTimestamp" in entry:
                    sample["timestamp"] = entry["startTimestamp"]  # epoch ms

                for key, idx in key_index.items():
                    if idx < len(entry["metrics"]):
                        val = entry["metrics"][idx]
                        if val is not None:
                            sample[key] = val

                if sample:
                    result["metrics"].append(sample)

            logger.info(
                f"Extracted {len(result['metrics'])} metric samples for activity {activity_id}"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to fetch activity samples: {e}")
            return None
