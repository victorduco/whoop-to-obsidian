"""Whoop API client for fetching health metrics."""

import logging
import time
from typing import Optional

import requests

from .exceptions import WhoopAPIError
from .models import WhoopConfig, WhoopMetrics

logger = logging.getLogger(__name__)


class WhoopClient:
    """Client for interacting with Whoop API."""

    def __init__(self, config: WhoopConfig, api_token: str):
        """
        Initialize Whoop API client.

        Args:
            config: Whoop configuration object.
            api_token: Bearer token for API authentication.
        """
        self.config = config
        self.api_token = api_token
        self.base_url = config.base_url.rstrip("/")
        self.timeout = config.timeout_seconds
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        }

    def _make_request(
        self, endpoint: str, max_retries: int = 3
    ) -> dict:
        """
        Make HTTP request to Whoop API with retry logic.

        Args:
            endpoint: API endpoint path (without base URL).
            max_retries: Maximum number of retry attempts.

        Returns:
            JSON response as dictionary.

        Raises:
            WhoopAPIError: If request fails after all retries.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        for attempt in range(max_retries):
            try:
                logger.debug(f"Making request to {url} (attempt {attempt + 1}/{max_retries})")
                response = requests.get(
                    url, headers=self.headers, timeout=self.timeout
                )

                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 2 ** attempt))
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
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                raise WhoopAPIError(f"Request timeout after {max_retries} attempts")

            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Connection error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise WhoopAPIError(f"Connection failed after {max_retries} attempts: {e}")

            except requests.exceptions.HTTPError as e:
                raise WhoopAPIError(f"HTTP error: {e}")

            except requests.exceptions.RequestException as e:
                raise WhoopAPIError(f"Request failed: {e}")

        raise WhoopAPIError(f"Request failed after {max_retries} attempts")

    def fetch_today_metrics(self) -> WhoopMetrics:
        """
        Fetch today's health metrics from Whoop API.

        Returns:
            WhoopMetrics object with available metrics.

        Raises:
            WhoopAPIError: If API request fails.
        """
        # Note: The actual endpoint and response structure will depend on
        # the real Whoop API. This is a placeholder implementation.
        # You'll need to adjust the endpoint and parsing based on actual API docs.

        try:
            # Example endpoint - adjust based on actual Whoop API
            response_data = self._make_request("metrics/today")

            # Parse response and extract metrics
            metrics_data = {}

            for metric_key in self.config.metrics:
                # Try to extract each configured metric
                value = self._extract_metric(response_data, metric_key)
                if value is not None:
                    metrics_data[metric_key] = value
                else:
                    logger.warning(f"Metric '{metric_key}' not found in API response")

            # Add timestamp if available
            if "timestamp" in response_data:
                metrics_data["timestamp"] = response_data["timestamp"]

            return WhoopMetrics(**metrics_data)

        except WhoopAPIError:
            raise
        except Exception as e:
            raise WhoopAPIError(f"Failed to parse API response: {e}")

    def _extract_metric(self, data: dict, metric_key: str) -> Optional[float]:
        """
        Extract a specific metric from API response.

        Args:
            data: API response data.
            metric_key: Metric key to extract.

        Returns:
            Metric value as float, or None if not found.
        """
        # This is a placeholder - adjust based on actual API structure
        # The API might nest metrics differently, e.g.:
        # - data['metrics'][metric_key]
        # - data['sleep']['score']
        # - etc.

        # Try direct access first
        if metric_key in data:
            return self._to_float(data[metric_key])

        # Try nested access
        if "metrics" in data and metric_key in data["metrics"]:
            return self._to_float(data["metrics"][metric_key])

        # Try mapping common metric names
        metric_mappings = {
            "sleep_score": ["sleep", "score"],
            "sleep_duration": ["sleep", "duration"],
            "recovery_score": ["recovery", "score"],
            "strain_score": ["strain", "score"],
            "hrv": ["hrv", "value"],
        }

        if metric_key in metric_mappings:
            current = data
            for key in metric_mappings[metric_key]:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return None
            return self._to_float(current)

        return None

    @staticmethod
    def _to_float(value) -> Optional[float]:
        """
        Convert value to float.

        Args:
            value: Value to convert.

        Returns:
            Float value or None if conversion fails.
        """
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

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
