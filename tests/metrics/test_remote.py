"""
Testing metrics/remote functionality
"""

import pytest

from almanack.metrics.remote import request_with_backoff


def test_request_with_backoff_resolves_doi() -> None:
    """
    Tests request_with_backoff resolves a real DOI endpoint.
    """

    doi_url = "https://doi.org/10.5281/zenodo.14888111"
    response = request_with_backoff(
        "HEAD",
        doi_url,
        headers={"accept": "application/json"},
        timeout=30,
        allow_redirects=True,
        max_retries=5,
        base_backoff=1,
        backoff_multiplier=2,
    )

    if response is None or response.status_code != 200:
        pytest.skip("DOI endpoint unavailable for live resolution check")

    assert response.status_code == 200
