"""Whoop API client for fetching health metrics."""

import logging
import time
from datetime import datetime, timedelta
from typing import Optional

import requests

from .exceptions import WhoopAPIError
from .models import (
    Cycle,
    Recovery,
    SleepActivity,
    WhoopCollectionResponse,
    WhoopConfig,
    WhoopMetrics,
)

logger = logging.getLogger(__name__)


class WhoopClient:
    """Client for interacting with Whoop API v2."""

    def __init__(self, config: WhoopConfig, api_token: str):
        """
        Initialize Whoop API client.

        Args:
            config: Whoop configuration object.
            api_token: Bearer token for API authentication (OAuth 2.0).
        """
        self.config = config
        self.api_token = api_token
        # Whoop API v2 base URL
        self.base_url = "https://api.prod.whoop.com/developer"
        self.timeout = config.timeout_seconds
        self.headers = {
            "Authorization": f"Bearer {api_token}",
        }

    def _make_request(
        self, endpoint: str, params: Optional[dict] = None, max_retries: int = 3
    ) -> dict:
        """
        Make HTTP request to Whoop API with retry logic.

        Args:
            endpoint: API endpoint path (without base URL).
            params: Optional query parameters.
            max_retries: Maximum number of retry attempts.

        Returns:
            JSON response as dictionary.

        Raises:
            WhoopAPIError: If request fails after all retries.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        for attempt in range(max_retries):
            try:
                logger.debug(
                    f"Making request to {url} (attempt {attempt + 1}/{max_retries})"
                )
                response = requests.get(
                    url, headers=self.headers, params=params, timeout=self.timeout
                )

                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 2**attempt))
                    logger.warning(
                        f"Rate limited by API. Retrying after {retry_after} seconds..."
                    )
                    time.sleep(retry_after)
                    continue

                # Handle authentication errors
                if response.status_code == 401:
                    raise WhoopAPIError(
                        "Authentication failed. Please check your WHOOP_API_TOKEN."
                    )

                # Raise for other HTTP errors
                response.raise_for_status()

                return response.json()

            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(2**attempt)  # Exponential backoff
                    continue
                raise WhoopAPIError(f"Request timeout after {max_retries} attempts")

            except requests.exceptions.ConnectionError as e:
                logger.warning(
                    f"Connection error (attempt {attempt + 1}/{max_retries}): {e}"
                )
                if attempt < max_retries - 1:
                    time.sleep(2**attempt)
                    continue
                raise WhoopAPIError(
                    f"Connection failed after {max_retries} attempts: {e}"
                )

            except requests.exceptions.HTTPError as e:
                raise WhoopAPIError(f"HTTP error: {e}")

            except requests.exceptions.RequestException as e:
                raise WhoopAPIError(f"Request failed: {e}")

        raise WhoopAPIError(f"Request failed after {max_retries} attempts")

    def get_sleep_collection(
        self, start: Optional[str] = None, end: Optional[str] = None, limit: int = 25
    ) -> list[SleepActivity]:
        """
        Get sleep activities from Whoop API v2.

        Args:
            start: Start date in ISO 8601 format (optional).
            end: End date in ISO 8601 format (optional).
            limit: Maximum number of records per page (default: 25).

        Returns:
            List of SleepActivity objects.

        Raises:
            WhoopAPIError: If API request fails.
        """
        params = {"limit": limit}
        if start:
            params["start"] = start
        if end:
            params["end"] = end

        try:
            data = self._make_request("v2/activity/sleep", params=params)
            records = data.get("records", [])
            return [SleepActivity(**record) for record in records]
        except Exception as e:
            logger.error(f"Failed to fetch sleep data: {e}")
            raise WhoopAPIError(f"Failed to fetch sleep data: {e}")

    def get_recovery_collection(
        self, start: Optional[str] = None, end: Optional[str] = None, limit: int = 25
    ) -> list[Recovery]:
        """
        Get recovery data from Whoop API v2.

        Args:
            start: Start date in ISO 8601 format (optional).
            end: End date in ISO 8601 format (optional).
            limit: Maximum number of records per page (default: 25).

        Returns:
            List of Recovery objects.

        Raises:
            WhoopAPIError: If API request fails.
        """
        params = {"limit": limit}
        if start:
            params["start"] = start
        if end:
            params["end"] = end

        try:
            data = self._make_request("v2/recovery", params=params)
            records = data.get("records", [])
            return [Recovery(**record) for record in records]
        except Exception as e:
            logger.error(f"Failed to fetch recovery data: {e}")
            raise WhoopAPIError(f"Failed to fetch recovery data: {e}")

    def get_cycle_collection(
        self, start: Optional[str] = None, end: Optional[str] = None, limit: int = 25
    ) -> list[Cycle]:
        """
        Get physiological cycles from Whoop API v2.

        Args:
            start: Start date in ISO 8601 format (optional).
            end: End date in ISO 8601 format (optional).
            limit: Maximum number of records per page (default: 25).

        Returns:
            List of Cycle objects.

        Raises:
            WhoopAPIError: If API request fails.
        """
        params = {"limit": limit}
        if start:
            params["start"] = start
        if end:
            params["end"] = end

        try:
            data = self._make_request("v2/cycle", params=params)
            records = data.get("records", [])
            return [Cycle(**record) for record in records]
        except Exception as e:
            logger.error(f"Failed to fetch cycle data: {e}")
            raise WhoopAPIError(f"Failed to fetch cycle data: {e}")

    def fetch_today_metrics(self) -> WhoopMetrics:
        """
        Fetch today's health metrics from Whoop API.

        Combines data from sleep, recovery, and cycle endpoints to create
        a unified metrics object for today's data.

        Returns:
            WhoopMetrics object with available metrics.

        Raises:
            WhoopAPIError: If API request fails.
        """
        # Calculate date range for today
        today = datetime.now()
        start_of_day = today.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        start_iso = start_of_day.isoformat() + "Z"
        end_iso = end_of_day.isoformat() + "Z"

        metrics_data = {}

        try:
            # Fetch sleep data
            sleep_activities = self.get_sleep_collection(
                start=start_iso, end=end_iso, limit=10
            )

            if sleep_activities:
                # Get most recent non-nap sleep
                main_sleep = None
                for sleep in sleep_activities:
                    if not sleep.nap and sleep.score_state == "SCORED":
                        main_sleep = sleep
                        break

                if main_sleep:
                    duration = main_sleep.get_duration_hours()
                    if duration is not None:
                        metrics_data["sleep_duration"] = duration

                    if main_sleep.score and main_sleep.score.sleep_performance_percentage:
                        metrics_data["sleep_score"] = (
                            main_sleep.score.sleep_performance_percentage
                        )

            # Fetch recovery data
            recoveries = self.get_recovery_collection(
                start=start_iso, end=end_iso, limit=10
            )

            if recoveries:
                # Get most recent recovery
                latest_recovery = None
                for recovery in recoveries:
                    if recovery.score_state == "SCORED":
                        latest_recovery = recovery
                        break

                if latest_recovery and latest_recovery.score:
                    score = latest_recovery.score
                    if score.recovery_score is not None:
                        metrics_data["recovery_score"] = score.recovery_score
                    if score.hrv_rmssd_milli is not None:
                        metrics_data["hrv"] = score.hrv_rmssd_milli

            # Fetch cycle data for strain
            cycles = self.get_cycle_collection(start=start_iso, end=end_iso, limit=10)

            if cycles:
                # Get most recent cycle
                latest_cycle = None
                for cycle in cycles:
                    if cycle.score_state == "SCORED":
                        latest_cycle = cycle
                        break

                if latest_cycle and latest_cycle.score:
                    if latest_cycle.score.strain is not None:
                        metrics_data["strain_score"] = latest_cycle.score.strain

            # Set timestamp
            metrics_data["timestamp"] = today.isoformat()

            return WhoopMetrics(**metrics_data)

        except WhoopAPIError:
            raise
        except Exception as e:
            raise WhoopAPIError(f"Failed to fetch today's metrics: {e}")

    def validate_metrics(self, metrics: WhoopMetrics) -> bool:
        """
        Validate that metrics are within expected ranges.

        Args:
            metrics: Metrics object to validate.

        Returns:
            True if validation passes, False otherwise.
        """
        validation_rules = {
            "sleep_score": (0, 100),
            "recovery_score": (0, 100),
            "strain_score": (0, 21),
            "sleep_duration": (0, 24),
            "hrv": (0, 300),
        }

        all_valid = True

        for metric_key, (min_val, max_val) in validation_rules.items():
            value = metrics.get_metric(metric_key)
            if value is not None:
                if not (min_val <= value <= max_val):
                    logger.warning(
                        f"Metric {metric_key}={value} is outside expected range "
                        f"[{min_val}, {max_val}]"
                    )
                    all_valid = False

        return all_valid
