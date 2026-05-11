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

    def get_activity_samples(self, activity_id: str) -> list[float]:
        """
        Fetch heart rate samples for a specific activity.

        Args:
            activity_id: Garmin activity ID

        Returns:
            List of heart rate values
        """
        if not self._authenticated:
            if not self.authenticate():
                return []

        try:
            # Garmin Connect API for activity samples
            # Try getting detailed activity data which includes samples
            details = self.client.get_activity_details(activity_id)

            # Extract heart rate from activityDetailMetrics
            # Find the correct index for directHeartRate from metricDescriptors
            if details and "activityDetailMetrics" in details and "metricDescriptors" in details:
                # Find index of directHeartRate
                hr_index = None
                for descriptor in details["metricDescriptors"]:
                    if descriptor.get("key") == "directHeartRate":
                        hr_index = descriptor.get("metricsIndex")
                        break
                
                if hr_index is None:
                    logger.warning(f"directHeartRate not found in metricDescriptors for {activity_id}")
                    return []
                
                hr_values = []
                for metric in details["activityDetailMetrics"]:
                    if "metrics" in metric and len(metric["metrics"]) > hr_index:
                        # Extract heart rate at the correct index
                        hr_value = metric["metrics"][hr_index]
                        if hr_value is not None and hr_value > 0:
                            # Filter out zero values and convert to int
                            hr_values.append(int(hr_value))

                logger.info(f"Fetched {len(hr_values)} heart rate samples for activity {activity_id} (index {hr_index})")
                return hr_values
            else:
                logger.warning(f"No activityDetailMetrics or metricDescriptors found for {activity_id}")
                return []

        except Exception as e:
            logger.error(f"Failed to fetch activity samples: {e}")
            return []

    def get_heart_rate_data(self, activity_id: str) -> list[dict]:
        """
        Fetch heart rate data for a specific activity.

        Args:
            activity_id: Garmin activity ID

        Returns:
            List of heart rate data points
        """
        if not self._authenticated:
            if not self.authenticate():
                return []

        try:
            # Garmin Connect API for heart rate zones
            hr_data = self.client.get_activity_hr_in_timezones(activity_id)
            logger.info(f"Fetched heart rate data for activity {activity_id}")
            return hr_data
        except Exception as e:
            logger.error(f"Failed to fetch heart rate data: {e}")
            return []
