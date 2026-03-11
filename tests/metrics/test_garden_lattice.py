"""
Tests for the Almanack's Garden Lattice specific functions.
"""

import pathlib
from datetime import datetime

import pygit2
import pytest

from almanack.metrics.garden_lattice import connectedness
from almanack.metrics.garden_lattice.connectedness import (
    detect_social_media_links,
    find_openalex_citing_projects_funding,
    find_software_mentions_openalex,
)
from tests.data.almanack.repo_setup.create_repo import repo_setup


@pytest.mark.parametrize(
    "content, expected",
    [
        # Test case: Single platform (Twitter)
        (
            "Follow us on Twitter: https://twitter.com/ourproject",
            {"social_media_platforms": ["Twitter"], "social_media_platforms_count": 1},
        ),
        # Test case: Multiple platforms
        (
            """Connect with us:
            - Twitter: https://twitter.com/ourproject
            - LinkedIn: https://linkedin.com/company/ourcompany
            - Discord: https://discord.gg/invitecode
            """,
            {
                "social_media_platforms": ["Discord", "LinkedIn", "Twitter"],
                "social_media_platforms_count": 3,
            },
        ),
        # Test case: No social media links
        (
            "This README.md contains no social media links.",
            {"social_media_platforms": [], "social_media_platforms_count": 0},
        ),
        # Test case: Duplicate platforms (should only count each platform once)
        (
            """Follow us:
            - Twitter: https://twitter.com/ourproject
            - Twitter: https://twitter.com/anotherproject
            """,
            {"social_media_platforms": ["Twitter"], "social_media_platforms_count": 1},
        ),
        # Test case: Less common platforms (Bluesky and Threads)
        (
            """Find us:
            - Bluesky: https://bsky.app/profile/ourproject
            - Threads: https://threads.net/ourproject
            """,
            {
                "social_media_platforms": ["Bluesky", "Threads"],
                "social_media_platforms_count": 2,
            },
        ),
        # Test case: Mixed case URLs (case-insensitive match)
        (
            """Stay connected:
            - YouTube: https://www.youtube.com/channel/OurChannel
            - Facebook: https://facebook.com/OurPage
            """,
            {
                "social_media_platforms": ["Facebook", "YouTube"],
                "social_media_platforms_count": 2,
            },
        ),
        # Test case: social media links without specific channels / users
        (
            """Stay connected:
            - YouTube: https://www.youtube.com
            - Facebook: https://facebook.com
            """,
            {
                "social_media_platforms": [],
                "social_media_platforms_count": 0,
            },
        ),
    ],
)
def test_detect_social_media_links(content, expected):
    result = detect_social_media_links(content)
    assert result == expected


def test_find_software_mentions_openalex_from_remote_url(
    tmp_path: pathlib.Path, monkeypatch
) -> None:
    """Test OpenAlex software mention search from remote URL-derived project name."""
    repo_setup(
        repo_path=tmp_path,
        files=[
            {"files": {"README.md": "example"}, "commit-date": datetime(2024, 1, 1)}
        ],
    )
    repo = pygit2.Repository(str(tmp_path))

    captured = {}

    def _fake_get_api_data(api_endpoint="https://api.openalex.org/works", params=None):
        captured["api_endpoint"] = api_endpoint
        captured["params"] = params
        return {
            "meta": {"count": 42},
            "results": [
                {
                    "id": "https://openalex.org/W1",
                    "display_name": "Work One",
                    "doi": "https://doi.org/10.1000/xyz",
                    "publication_year": 2024,
                    "cited_by_count": 7,
                }
            ],
        }

    monkeypatch.setattr(connectedness, "get_api_data", _fake_get_api_data)

    result = find_software_mentions_openalex(
        repo=repo, remote_url="https://github.com/software-gardening/almanack.git"
    )

    assert captured["api_endpoint"] == "https://api.openalex.org/works"
    assert captured["params"]["search"] == "almanack"
    assert result["query"] == "almanack"
    assert result["mentions_count"] == 42
    assert result["references"][0]["title"] == "Work One"


def test_find_software_mentions_openalex_from_local_repo_name(
    tmp_path: pathlib.Path, monkeypatch
) -> None:
    """Test OpenAlex software mention search falls back to local repo name."""
    repo_setup(
        repo_path=tmp_path,
        files=[
            {"files": {"README.md": "example"}, "commit-date": datetime(2024, 1, 1)}
        ],
    )
    repo = pygit2.Repository(str(tmp_path))

    captured = {}

    def _fake_get_api_data(api_endpoint="https://api.openalex.org/works", params=None):
        captured["api_endpoint"] = api_endpoint
        captured["params"] = params
        return {"meta": {"count": 3}, "results": []}

    monkeypatch.setattr(connectedness, "get_api_data", _fake_get_api_data)

    result = find_software_mentions_openalex(repo=repo, remote_url=None)

    assert captured["api_endpoint"] == "https://api.openalex.org/works"
    assert captured["params"]["search"] == tmp_path.name
    assert result["query"] == tmp_path.name
    assert result["mentions_count"] == 3
    assert result["references"] == []


def test_find_software_mentions_openalex_no_query() -> None:
    """Test OpenAlex software mention search returns empty defaults when no query can be derived."""

    class _RepoWithoutWorkdir:
        workdir = None

    result = find_software_mentions_openalex(
        repo=_RepoWithoutWorkdir(), remote_url=None
    )

    assert result == {"query": None, "mentions_count": None, "references": None}


def test_find_openalex_citing_projects_funding(monkeypatch) -> None:
    """Test OpenAlex funding aggregation for citing projects."""

    def _fake_get_api_data(api_endpoint="https://api.openalex.org/works", params=None):
        _ = api_endpoint, params
        return {
            "results": [
                {
                    "id": "https://openalex.org/W10",
                    "display_name": "Citing Work A",
                    "doi": "https://doi.org/10.1000/a",
                    "publication_year": 2022,
                    "cited_by_count": 12,
                    "grants": [
                        {"funder": "f1", "amount": 100},
                        {"funder": "f2", "amount": 50, "currency": "USD"},
                    ],
                },
                {
                    "id": "https://openalex.org/W11",
                    "display_name": "Citing Work B",
                    "doi": "https://doi.org/10.1000/b",
                    "publication_year": 2023,
                    "cited_by_count": 5,
                    "grants": [],
                    "funders": [{"id": "https://openalex.org/F3"}],
                },
            ]
        }

    monkeypatch.setattr(connectedness, "get_api_data", _fake_get_api_data)
    result = find_openalex_citing_projects_funding(
        openalex_work_id="https://openalex.org/W123"
    )

    assert result["source_work_id"] == "https://openalex.org/W123"
    assert result["citing_works_count_total"] == 0
    assert result["citing_works_count_sampled"] == 2
    assert result["citing_works_with_grants_count"] == 1
    assert result["citing_projects_grants_count_sampled"] == 2
    assert result["citing_projects_award_amount_usd_total_sampled"] == 150
    assert result["citing_projects_funding_sources_count_sampled"] == 2
    assert result["citing_projects_unique_funders_count_sampled"] == 3
    assert result["citing_projects_unique_funders_sampled"] == [
        "f1",
        "f2",
        "https://openalex.org/F3",
    ]
    assert result["references"][0]["title"] == "Citing Work A"
    assert result["references"][0]["award_amount_usd_total"] == 150
