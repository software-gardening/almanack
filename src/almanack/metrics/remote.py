"""
This module focuses on remote API requests
and related aspects.
"""

import logging
import os
import pathlib
import time
from datetime import datetime, timezone
from typing import Dict, Optional, Set

import requests

LOGGER = logging.getLogger(__name__)

METRICS_TABLE = f"{pathlib.Path(__file__).parent!s}/metrics.yml"
DATETIME_NOW = datetime.now(timezone.utc)


def request_with_backoff(  # noqa: PLR0913
    method: str,
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, str]] = None,
    timeout: int = 30,
    allow_redirects: Optional[bool] = None,
    max_retries: int = 8,
    base_backoff: float = 2.0,
    backoff_multiplier: float = 2.0,
    retry_statuses: Optional[Set[int]] = None,
) -> Optional[requests.Response]:
    """
    Perform an HTTP request with retry using
    a backoff for transient failures.

    Args:
        method (str): The HTTP method to use (e.g., "GET", "HEAD").
        url (str): The URL to request.
        headers (Optional[Dict[str, str]]): Optional HTTP headers.
        params (Optional[Dict[str, str]]): Optional query parameters.
        timeout (int): Request timeout in seconds.
        allow_redirects (Optional[bool]): Whether to follow redirects.
        max_retries (int): Maximum number of attempts before giving up.
        base_backoff (float): Base backoff duration in seconds.
        backoff_multiplier (float): Multiplier for exponential backoff growth.
        retry_statuses (Optional[Set[int]]): HTTP status codes to retry.

    Returns:
        Optional[requests.Response]: The response on success, or None on failure.
    """
    if retry_statuses is None:
        retry_statuses = {429, 500, 502, 503, 504}

    for attempt in range(1, max_retries + 1):
        try:
            request_kwargs = {
                "method": method,
                "url": url,
                "headers": headers,
                "params": params,
                "timeout": timeout,
            }
            if allow_redirects is not None:
                request_kwargs["allow_redirects"] = allow_redirects
            # Attempt the request; retry on transient failures.
            response = requests.request(**request_kwargs)
            if response.status_code in retry_statuses and attempt < max_retries:
                # Exponential backoff limits repeated transient failures.
                backoff = base_backoff * (backoff_multiplier ** (attempt - 1))
                LOGGER.warning(
                    f"Transient HTTP {response.status_code} for {url} "
                    f"(attempt {attempt}/{max_retries}). Retrying in {backoff} seconds..."
                )
                time.sleep(backoff)
                continue
            return response
        except requests.RequestException as reqe:
            if attempt < max_retries:
                backoff = base_backoff * (backoff_multiplier ** (attempt - 1))
                LOGGER.warning(
                    f"Request error for {url} (attempt {attempt}/{max_retries}): {reqe}. "
                    f"Retrying in {backoff} seconds..."
                )
                time.sleep(backoff)
                continue
            LOGGER.warning(
                f"Request failed for {url} after {max_retries} attempts: {reqe}"
            )
            return None

    return None


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

    # If available, use GitHub token for authenticated requests to increase rate limits
    github_token = os.environ.get("GITHUB_TOKEN")
    headers = {"accept": "application/json"}
    if github_token and (
        "github.com" in api_endpoint or "api.github.com" in api_endpoint
    ):
        headers["Authorization"] = f"Bearer {github_token}"
    else:
        headers = {"accept": "application/json"}

    max_retries = 100  # Number of attempts for rate limit errors
    base_backoff = 5  # Base backoff time in seconds

    for attempt in range(1, max_retries + 1):
        try:
            # Perform the GET request with query parameters
            response = request_with_backoff(
                "GET",
                api_endpoint,
                headers=headers,
                params=params,
                timeout=300,
                max_retries=3,
                base_backoff=2,
                backoff_multiplier=2,
            )
            if response is None:
                return {}

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
