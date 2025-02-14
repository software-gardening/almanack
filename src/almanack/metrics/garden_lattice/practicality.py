"""
This module focuses on the Almanack's Garden Lattice materials
which involve how people can apply software in practice.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

import pygit2

from almanack.metrics.remote import get_api_data

LOGGER = logging.getLogger(__name__)


def count_repo_tags(repo: pygit2.Repository, since: Optional[datetime] = None) -> int:
    """
    Counts the number of tags in a pygit2 repository.

    If a `since` datetime is provided, counts only tags associated
    with commits made after the specified datetime. Otherwise,
    counts all tags in the repository.

    Args:
        repo (pygit2.Repository):
            The repository to analyze.
        since (Optional[datetime]):
            The cutoff datetime. Only tags for commits after
            this datetime are counted. If None, all tags are counted.

    Returns:
        int:
            The number of tags in the repository that meet the criteria.
    """
    since_timestamp = since.timestamp() if since else 0

    count = 0
    for ref in repo.references:
        if ref.startswith("refs/tags/"):
            tag = repo.lookup_reference(ref)
            target_commit = repo[tag.target]

            # Consider lightweight or annotated tags
            if target_commit.type == pygit2.GIT_OBJECT_TAG:
                target_commit = repo[target_commit.target]

            # Check commit timestamp against `since`
            if target_commit.commit_time > since_timestamp:
                count += 1

    return count


def get_ecosystems_package_metrics(repo_url: str) -> Dict[str, Any]:
    """
    Fetches package data from the ecosyste.ms API and calculates metrics
    about the number of unique ecosystems, total version counts,
    and the list of ecosystem names.

    Args:
        repo_url (str):
            The repository URL of the package to query.

    Returns:
        Dict[str, Any]:
            A dictionary containing information about packages
            related to the repository.
    """

    if repo_url is None:
        LOGGER.info(
            "Did not receive a valid repository URL and unable to gather package metrics."
        )
        return {}

    # normalize http to https if necessary
    if repo_url.startswith("http://"):
        LOGGER.info(
            "Received `http://` repository URL for package metrics search. Normalizing to use `https://`."
        )
        repo_url = repo_url.replace("http://", "https://")

    # normalize git@ ssh links to https if necessary
    if repo_url.startswith("git@"):
        LOGGER.warning(
            "Received `git@` repository URL for package metrics search. Normalizing to use `https://`."
        )
        domain, path = repo_url[4:].split(":", 1)
        repo_url = f"https://{domain}/{path}".removesuffix(".git")

    # perform packages request on the ecosyste.ms API
    package_data = get_api_data(
        api_endpoint="https://packages.ecosyste.ms/api/v1/packages/lookup",
        params={"repository_url": repo_url},
    )

    # Initialize counters
    ecosystems = set()
    total_versions = 0

    for entry in package_data:
        # count ecosystems
        if "ecosystem" in entry:
            ecosystems.add(entry["ecosystem"])

        # sum versions
        total_versions += entry.get("versions_count", 0)

    return {
        "ecosystems_count": len(ecosystems),
        "versions_count": total_versions,
        "ecosystems_names": sorted(ecosystems),
    }
