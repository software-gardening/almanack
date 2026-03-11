"""
Module for Almanack metrics covering human connection and engagement
in software projects such as contributor activity, collaboration
frequency.
"""

import logging
import pathlib
import re
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import pygit2
import requests
import yaml
from currency_converter import CurrencyConverter
from currency_converter.currency_converter import RateNotFoundError

from almanack.git import file_exists_in_repo, find_file, read_file
from almanack.metrics.remote import get_api_data, request_with_backoff

LOGGER = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_currency_converter() -> CurrencyConverter:
    """Return a cached currency converter for award amount normalization."""
    return CurrencyConverter()


def _get_work_awards(work_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return award-like records from OpenAlex work payloads.

    Supports both modern `awards` and legacy `grants` fields.
    """
    awards = work_data.get("awards")
    if awards is None:
        awards = work_data.get("grants")
    return awards if isinstance(awards, list) else []


def _extract_funder_key(funder: Any) -> Optional[str]:
    """Extract a stable funder key from known OpenAlex funder shapes."""
    if isinstance(funder, str):
        return funder
    if isinstance(funder, dict):
        return (
            funder.get("id")
            or funder.get("funder")
            or funder.get("display_name")
            or funder.get("name")
        )
    return None


def _award_amount_to_usd(amount: Any, currency: Optional[str]) -> Optional[float]:
    """Convert an award amount to USD; assume USD when currency is unavailable."""
    if amount is None:
        return None
    try:
        numeric_amount = float(amount)
    except (TypeError, ValueError):
        return None

    source_currency = (currency or "USD").upper()
    if source_currency == "USD":
        return numeric_amount

    try:
        return float(
            _get_currency_converter().convert(numeric_amount, source_currency, "USD")
        )
    except (RateNotFoundError, ValueError):
        LOGGER.debug(
            "Could not convert award amount to USD for currency '%s'.",
            source_currency,
        )
        return None


def _summarize_openalex_funding(work_data: Dict[str, Any]) -> Dict[str, Any]:
    """Summarize OpenAlex funding payloads for one work record."""
    if not isinstance(work_data, dict):
        work_data = {}
    awards = _get_work_awards(work_data)
    unique_funders = set()
    funding_sources_count = 0
    awards_with_amount_count = 0
    award_amount_usd_total = 0.0

    for award in awards:
        if not isinstance(award, dict):
            continue

        funder_key = _extract_funder_key(award.get("funder"))
        if funder_key:
            funding_sources_count += 1
            unique_funders.add(funder_key)

        usd_amount = _award_amount_to_usd(award.get("amount"), award.get("currency"))
        if usd_amount is not None:
            awards_with_amount_count += 1
            award_amount_usd_total += usd_amount

    for funder in work_data.get("funders") or []:
        funder_key = _extract_funder_key(funder)
        if funder_key:
            unique_funders.add(funder_key)

    return {
        "awards": awards,
        "awards_count": len(awards),
        "awards_with_amount_count": awards_with_amount_count,
        "award_amount_usd_total": award_amount_usd_total,
        "funding_sources_count": funding_sources_count,
        "unique_funders_count": len(unique_funders),
        "unique_funders": sorted(unique_funders),
    }


def _extract_doi_from_citation_data(citation_data: Dict[str, Any]) -> Optional[str]:
    """Extract a DOI value from parsed CITATION.cff payload."""
    if "doi" in citation_data:
        return citation_data.get("doi")
    if "identifiers" in citation_data:
        return next(
            (
                identifier["value"]
                for identifier in citation_data.get("identifiers", [])
                if identifier.get("type") == "doi"
            ),
            None,
        )
    return None


def _build_openalex_doi_metrics(openalex_result: Dict[str, Any]) -> Dict[str, Any]:
    """Build DOI-linked OpenAlex metrics for storage in citation results."""
    publication_date = openalex_result.get("publication_date")
    funding_summary = _summarize_openalex_funding(openalex_result)
    return {
        "openalex_work_id": openalex_result.get("id", None),
        "publication_date": (
            # note: we cast to date for consistent use throughout
            # the almanack as a "date" and not "datetime" type.
            datetime.strptime(publication_date, "%Y-%m-%d").date()
            if publication_date is not None
            else None
        ),
        "cited_by_count": openalex_result.get("cited_by_count", None),
        "fwci": openalex_result.get("fwci", None),
        "is_not_retracted": (
            None
            if openalex_result.get("is_retracted") is None
            else not openalex_result["is_retracted"]
        ),
        "awards": funding_summary["awards"],
        "awards_count": funding_summary["awards_count"],
        "awards_with_amount_count": funding_summary["awards_with_amount_count"],
        "award_amount_usd_total": funding_summary["award_amount_usd_total"],
        "funding_sources_count": funding_summary["funding_sources_count"],
        "unique_funders_count": funding_summary["unique_funders_count"],
        "unique_funders": funding_summary["unique_funders"],
        # Legacy aliases retained for compatibility.
        "grants": funding_summary["awards"],
        "grants_count": funding_summary["awards_count"],
    }


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


def is_citable(repo: pygit2.Repository) -> bool:
    """
    Check if the given repository is citable.

    A repository is considered citable if it contains a CITATION.cff or CITATION.bib
    file, or if the README.md file contains a citation section indicated by "## Citation"
    or "## Citing".

    Args:
        repo (pygit2.Repository): The repository to check for citation files.

    Returns:
        bool: True if the repository is citable, False otherwise.
    """

    # Check for a CITATION.cff or CITATION.bib file
    if file_exists_in_repo(
        repo=repo,
        expected_file_name="citation",
        check_extension=True,
        extensions=[".cff", ".bib"],
    ):
        return True

    # Look for a README.md file and read its content
    readme_file = find_file(repo=repo, filepath="readme", case_insensitive=True)
    if (
        readme_file is not None
        and (file_content := read_file(repo=repo, entry=readme_file)) is not None
    ):
        # Check for an H2 heading indicating a citation section
        if any(
            check_string in file_content
            for check_string in [
                # markdown sub-headers
                "## Citation",
                "## Citing",
                "## Cite",
                "## How to cite",
                # RST sub-headers
                "Citation\n--------",
                "Citing\n------",
                "Cite\n----",
                "How to cite\n-----------",
                # DOI shield
                "[![DOI](https://img.shields.io/badge/DOI",
            ]
        ):
            return True

    return False


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
        "openalex_work_id": None,
        "valid_format_doi": None,
        "https_resolvable_doi": None,
        "publication_date": None,
        "cited_by_count": None,
        "fwci": None,
        "is_not_retracted": None,
        "awards": None,
        "awards_count": None,
        "awards_with_amount_count": None,
        "award_amount_usd_total": None,
        "funding_sources_count": None,
        "unique_funders_count": None,
        "unique_funders": None,
        "grants": None,
        "grants_count": None,
    }

    # Find the CITATION.cff file
    if (citationcff_file := find_file(repo=repo, filepath="CITATION.cff")) is None:
        LOGGER.info("No CITATION.cff file discovered.")
        return result

    try:
        # Read and parse the CITATION.cff file
        citation_data = (
            yaml.safe_load(read_file(repo=repo, entry=citationcff_file)) or {}
        )
        result["doi"] = _extract_doi_from_citation_data(citation_data)
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
                # Use backoff to reduce the chance that a DOI HTTP request
                # fails due to rate limiting or transient network issues.
                response = request_with_backoff(
                    "HEAD",
                    f"https://doi.org/{result['doi']}",
                    headers={"accept": "application/json"},
                    allow_redirects=True,
                    max_retries=3,
                )
                # if we have a response and the response is code 200
                # also known as HTTP OK, then the DOI resolves properly
                if (
                    response is not None
                    and response.status_code == 200  # noqa: PLR2004
                ):
                    result["https_resolvable_doi"] = True
                else:
                    status_code = (
                        response.status_code if response is not None else "unknown"
                    )
                    LOGGER.warning(
                        "DOI does not resolve properly: "
                        f"https://doi.org/{result['doi']} (status {status_code})"
                    )
                    result["https_resolvable_doi"] = False

            except requests.RequestException as e:
                LOGGER.warning(f"Error resolving DOI: {e}")
                result["https_resolvable_doi"] = False

            # Perform exact DOI lookup on OpenAlex
            try:
                openalex_result = (
                    get_api_data(
                        api_endpoint=f"https://api.openalex.org/works/doi:{result['doi']}"
                    )
                    or {}
                )
                result.update(_build_openalex_doi_metrics(openalex_result))
            except requests.RequestException as e:
                LOGGER.warning(f"Error during OpenAlex exact DOI lookup: {e}")

    return result


def find_software_mentions_openalex(
    repo: pygit2.Repository,
    remote_url: Optional[str],
    max_references: int = 10,
) -> Dict[str, Any]:
    """Find OpenAlex works that mention a repository by software/project name.

    Args:
        repo: Repository used for software name discovery when no remote URL
            is available.
        remote_url: Remote repository URL used to derive the project name.
        max_references: Maximum number of matching works to include in results.

    Returns:
        Dictionary containing the query name, aggregate mention count, and
        a minimal list of matching works from OpenAlex.
    """
    project_name = None
    if remote_url:
        parsed = urlparse(remote_url)
        path_name = pathlib.Path(parsed.path.rstrip("/")).name
        project_name = path_name.removesuffix(".git") if path_name else None
    if not project_name:
        # Fallback for local-only repositories.
        if getattr(repo, "workdir", None):
            project_name = pathlib.Path(repo.workdir.rstrip("/")).name
        elif getattr(repo, "path", None):
            project_name = pathlib.Path(repo.path.rstrip("/")).parent.name
        if project_name:
            project_name = project_name.removesuffix(".git")

    result = {
        "query": project_name,
        "mentions_count": None,
        "references": None,
    }
    if not project_name:
        return result

    openalex_result = get_api_data(
        api_endpoint="https://api.openalex.org/works",
        params={
            "search": project_name,
            "per-page": str(max_references),
            "sort": "cited_by_count:desc",
        },
    )
    if not openalex_result:
        return result

    works = openalex_result.get("results", [])
    references = [
        {
            "id": work.get("id"),
            "title": work.get("display_name"),
            "doi": work.get("doi"),
            "publication_year": work.get("publication_year"),
            "cited_by_count": work.get("cited_by_count"),
        }
        for work in works
    ]
    result["mentions_count"] = openalex_result.get("meta", {}).get("count", 0)
    result["references"] = references
    return result


def find_openalex_indirect_funding(
    openalex_work_id: Optional[str],
    max_references: int = 25,
) -> Dict[str, Any]:
    """Find funding signals from OpenAlex works that cite the project work.

    "Indirect funding" here means funding attached to downstream citing works
    in the OpenAlex network, not grant indirect cost rates/overhead.

    Args:
        openalex_work_id: OpenAlex work identifier for the direct project work.
        max_references: Maximum number of citing works to query from OpenAlex.

    Returns:
        Dictionary with sampled citing-work funding aggregates and references.
    """
    result = {
        "source_work_id": openalex_work_id,
        "citing_works_count_total": None,
        "citing_works_count_sampled": None,
        "citing_works_with_grants_count": None,
        "indirect_grants_count_sampled": None,
        "indirect_award_amount_usd_total_sampled": None,
        "indirect_funding_sources_count_sampled": None,
        "indirect_unique_funders_count_sampled": None,
        "indirect_unique_funders_sampled": None,
        "sample_limit": max_references,
        "references": None,
    }
    if not openalex_work_id:
        return result

    cited_work_key = openalex_work_id.rstrip("/").split("/")[-1]
    openalex_result = get_api_data(
        api_endpoint="https://api.openalex.org/works",
        params={
            "filter": f"cites:{cited_work_key}",
            "per-page": str(max_references),
            "sort": "cited_by_count:desc",
        },
    )
    if not openalex_result:
        return result

    works = openalex_result.get("results", [])
    result["citing_works_count_total"] = openalex_result.get("meta", {}).get("count", 0)
    references = []
    grants_total = 0
    works_with_grants = 0
    funding_sources_total = 0
    award_amount_usd_total = 0.0
    unique_funders = set()
    for work in works:
        funding_summary = _summarize_openalex_funding(work)
        grants_count = funding_summary["awards_count"]
        grants_total += grants_count
        if grants_count > 0:
            works_with_grants += 1
        funding_sources_total += funding_summary["funding_sources_count"]
        award_amount_usd_total += funding_summary["award_amount_usd_total"]
        unique_funders.update(funding_summary["unique_funders"])
        references.append(
            {
                "id": work.get("id"),
                "title": work.get("display_name"),
                "doi": work.get("doi"),
                "publication_year": work.get("publication_year"),
                "cited_by_count": work.get("cited_by_count"),
                "grants_count": grants_count,
                "award_amount_usd_total": funding_summary["award_amount_usd_total"],
                "funding_sources_count": funding_summary["funding_sources_count"],
                "unique_funders_count": funding_summary["unique_funders_count"],
            }
        )

    result["citing_works_count_sampled"] = len(works)
    result["citing_works_with_grants_count"] = works_with_grants
    result["indirect_grants_count_sampled"] = grants_total
    result["indirect_award_amount_usd_total_sampled"] = award_amount_usd_total
    result["indirect_funding_sources_count_sampled"] = funding_sources_total
    result["indirect_unique_funders_count_sampled"] = len(unique_funders)
    result["indirect_unique_funders_sampled"] = sorted(unique_funders)
    result["references"] = references
    return result
