"""
This module focuses on the Almanack's Garden Lattice materials
which focus on elements of human connection and engagement.
"""

import logging
import pathlib
import re 

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import defusedxml.ElementTree as ET
import pygit2
import requests
import yaml

from ...git import (
    clone_repository,
    count_files,
    find_file,
    get_commits,
    get_edited_files,
    get_remote_url,
    read_file,
    file_exists_in_repo
)

from ..remote import get_api_data
from ..entropy.calculate_entropy import (
    calculate_aggregate_entropy,
    calculate_normalized_entropy,
)


LOGGER = logging.getLogger(__name__)


def default_branch_is_not_master(repo: pygit2.Repository) -> bool:
    """
    Checks if the default branch of the specified
    repository is "master".

    Args:
        repo (Repository):
            A pygit2.Repository object representing the Git repository.

    Returns:
        bool:
            True if the default branch is "master", False otherwise.
    """
    # Access the "refs/remotes/origin/HEAD" reference to find the default branch
    try:
        # check whether remote head and remote master are the same
        return (
            repo.references.get("refs/remotes/origin/HEAD").target
            == repo.references.get("refs/remotes/origin/master").target
        )

    except AttributeError:
        # If "refs/remotes/origin/HEAD" or "refs/remotes/origin/master" doesn't exist,
        # fall back to the local HEAD check
        return repo.head.shorthand != "master"

def count_unique_contributors(
    repo: pygit2.Repository, since: Optional[datetime] = None
) -> int:
    """
    Counts the number of unique contributors to a repository.

    If a `since` datetime is provided, counts contributors
    who made commits after the specified datetime.
    Otherwise, counts all contributors.

    Args:
        repo (pygit2.Repository):
            The repository to analyze.
        since (Optional[datetime]):
            The cutoff datetime. Only contributions after
            this datetime are counted. If None, all
            contributions are considered.

    Returns:
        int:
            The number of unique contributors.
    """
    since_timestamp = since.timestamp() if since else 0
    contributors = {
        commit.author.email
        for commit in repo.walk(repo.head.target, pygit2.GIT_SORT_TIME)
        if commit.commit_time > since_timestamp
    }
    return len(contributors)

def detect_social_media_links(content: str) -> Dict[str, List[str]]:
    """
    Analyzes README.md content to identify social media links.

    Args:
        readme_content (str):
            The content of the README.md file as a string.

    Returns:
        Dict[str, List[str]]:
            A dictionary containing social media details
            discovered from readme.md content.
    """
    # Define patterns for social media links
    social_media_patterns = {
        "Twitter": r"https?://(?:www\.)?twitter\.com/[\w]+",
        "LinkedIn": r"https?://(?:www\.)?linkedin\.com/(?:in|company)/[\w-]+",
        "YouTube": r"https?://(?:www\.)?youtube\.com/(?:channel|c|user)/[\w-]+",
        "Facebook": r"https?://(?:www\.)?facebook\.com/[\w.-]+",
        "Instagram": r"https?://(?:www\.)?instagram\.com/[\w.-]+",
        "TikTok": r"https?://(?:www\.)?tiktok\.com/@[\w.-]+",
        "Discord": r"https?://(?:www\.)?discord(?:\.gg|\.com/invite)/[\w-]+",
        "Slack": r"https?://[\w.-]+\.slack\.com",
        "Gitter": r"https?://gitter\.im/[\w/-]+",
        "Telegram": r"https?://(?:www\.)?t\.me/[\w-]+",
        "Mastodon": r"https?://[\w.-]+/users/[\w-]+",
        "Threads": r"https?://(?:www\.)?threads\.net/[\w.-]+",
        "Bluesky": r"https?://(?:www\.)?bsky\.app/profile/[\w.-]+",
    }

    # Initialize results
    found_platforms = set()

    # Search for social media links
    for platform, pattern in social_media_patterns.items():
        if re.search(pattern, content, re.IGNORECASE):
            found_platforms.add(platform)

    return {
        "social_media_platforms": sorted(found_platforms),
        "social_media_platforms_count": len(found_platforms),
    }

def find_doi_citation_data(repo: pygit2.Repository) -> Dict[str, Any]:
    """
    Find and validate DOI information from a CITATION.cff
    file in a repository.

    This function searches for a `CITATION.cff` file in the provided repository,
    extracts the DOI (if available), validates its format, checks its
    resolvability via HTTP, and performs an exact DOI lookup on the OpenAlex API.

    Args:
        repo (pygit2.Repository):
            The repository object to search for the CITATION.cff file.

    Returns:
        Dict[str, Any]:
            A dictionary containing DOI-related information and metadata.
    """

    result = {
        "doi": None,
        "valid_format_doi": None,
        "https_resolvable_doi": None,
        "publication_date": None,
        "cited_by_count": None,
    }

    # Find the CITATION.cff file
    if (citationcff_file := find_file(repo=repo, filepath="CITATION.cff")) is None:
        LOGGER.warning("No CITATION.cff file discovered.")
        return result

    try:
        # Read and parse the CITATION.cff file
        citation_data = yaml.safe_load(read_file(repo=repo, entry=citationcff_file))

        # Extract DOI from 'doi' or 'identifiers' field
        if "doi" in citation_data.keys():
            result["doi"] = citation_data.get("doi", None)
        elif "identifiers" in citation_data.keys():
            result["doi"] = next(
                (
                    identifier["value"]
                    for identifier in citation_data.get("identifiers", [])
                    if identifier.get("type") == "doi"
                ),
                None,
            )
    except yaml.YAMLError as e:
        LOGGER.warning(f"Error reading YAML: {e}")

    if result["doi"]:
        # Validate the DOI format
        result["valid_format_doi"] = bool(
            re.match(r"^10\.\d{4,9}/[-._;()/:A-Za-z0-9]+$", result["doi"])
        )
        if result["valid_format_doi"]:
            try:
                # Check DOI resolvability via HTTPS
                if (
                    requests.head(
                        f"https://doi.org/{result['doi']}",
                        allow_redirects=True,
                        timeout=30,
                    ).status_code
                    == 200  # noqa: PLR2004
                ):
                    result["https_resolvable_doi"] = True
                else:
                    LOGGER.warning(
                        f"DOI does not resolve properly: https://doi.org/{result['doi']}"
                    )
                    result["https_resolvable_doi"] = False

            except requests.RequestException as e:
                LOGGER.warning(f"Error resolving DOI: {e}")
                result["https_resolvable_doi"] = False

            # Perform exact DOI lookup on OpenAlex
            try:
                openalex_result = get_api_data(
                    api_endpoint=f"https://api.openalex.org/works/doi:{result['doi']}"
                )
                publication_date = openalex_result.get("publication_date", None)
                result.update(
                    {
                        "publication_date": (
                            datetime.strptime(publication_date, "%Y-%m-%d")
                            if publication_date is not None
                            else None
                        ),
                        "cited_by_count": openalex_result.get("cited_by_count", None),
                    }
                )
            except requests.RequestException as e:
                LOGGER.warning(f"Error during OpenAlex exact DOI lookup: {e}")

    return result
