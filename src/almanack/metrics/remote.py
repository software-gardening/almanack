"""
This module focuses on remote API requests
and related aspects.
"""

import logging
import pathlib
import time
from datetime import datetime, timezone
from typing import Dict, Optional

import requests

LOGGER = logging.getLogger(__name__)

METRICS_TABLE = f"{pathlib.Path(__file__).parent!s}/metrics.yml"
DATETIME_NOW = datetime.now(timezone.utc)


def get_api_data(
    api_endpoint: str = "https://repos.ecosyste.ms/api/v1/repositories/lookup",
    params: Optional[Dict[str, str]] = None,
) -> dict:
    """
    Get data from an API based on the remote URL, with retry logic for GitHub rate limiting.

    Args:
        api_endpoint (str):
            The HTTP API endpoint to use for the request.
        params (Optional[Dict[str, str]])
             Additional query parameters to include in the GET request.

    Returns:
        dict: The JSON response from the API as a dictionary.

    Raises:
        requests.RequestException: If the API call fails for reasons other than rate limiting.
    """
    if params is None:
        params = {}

    max_retries = 100  # Number of attempts for rate limit errors
    base_backoff = 5  # Base backoff time in seconds

    for attempt in range(1, max_retries + 1):
        try:
            # Perform the GET request with query parameters
            response = requests.get(
                api_endpoint,
                headers={"accept": "application/json"},
                params=params,
                timeout=300,
            )

            # Raise an exception for HTTP errors
            response.raise_for_status()

            # Parse and return the JSON response
            return response.json()

        except requests.HTTPError as httpe:
            # Check for rate limit error (403 with a rate limit header)
            if (
                response.status_code == 403  # noqa: PLR2004
                and "X-RateLimit-Remaining" in response.headers
            ):
                if attempt < max_retries:
                    # Calculate backoff time multiplied by attempt number
                    # (linear growth)
                    backoff = base_backoff * (attempt - 1)
                    LOGGER.warning(
                        f"Rate limit exceeded (attempt {attempt}/{max_retries}). "
                        f"Retrying in {backoff} seconds..."
                    )
                    time.sleep(backoff)
                else:
                    LOGGER.info("Rate limit exceeded. All retry attempts exhausted.")
                    return {}
            else:
                # Raise other HTTP errors immediately
                LOGGER.info(f"Unexpected HTTP error: {httpe}")
                return {}
        except requests.RequestException as reqe:
            # Raise other non-HTTP exceptions immediately
            LOGGER.info(f"Unexpected request error: {reqe}")
            return {}

    LOGGER.info("All retries failed. Returning an empty response.")
    return {}  # Default return in case all retries fail
