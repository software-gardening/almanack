"""
This module computes data for GitHub Repositories
"""

import json
import logging
import pathlib
import re
import shutil
import tempfile
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse

import defusedxml.ElementTree as ET
import pygit2
import requests
import yaml

from ..git import (
    clone_repository,
    count_files,
    find_file,
    get_commits,
    get_edited_files,
    get_remote_url,
    read_file,
)
from .entropy.calculate_entropy import (
    calculate_aggregate_entropy,
    calculate_normalized_entropy,
)

LOGGER = logging.getLogger(__name__)

METRICS_TABLE = f"{pathlib.Path(__file__).parent!s}/metrics.yml"
DATETIME_NOW = datetime.now(timezone.utc)


def get_table(repo_path: str) -> List[Dict[str, Any]]:
    """
    Gather metrics on a repository and return the results in a structured format.

    This function reads a metrics table from a predefined YAML file, computes relevant
    data from the specified repository, and associates the computed results with
    the metrics defined in the metrics table. If an error occurs during data
    computation, an exception is raised.

    Args:
        repo_path (str): The file path to the repository for which metrics are
        to be performed.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries containing the metrics and
        their associated results. Each dictionary includes the original metrics data
        along with the computed result under the key "result".

    Raises:
        ReferenceError: If there is an error encountered while processing the
        data, providing context in the error message.
    """

    # read the metrics table
    with open(METRICS_TABLE, "r") as f:
        metrics_table = yaml.safe_load(f)["metrics"]

    # gather data for use in the metrics table
    data = compute_repo_data(repo_path=repo_path)

    if "error" in data.keys():
        raise ReferenceError("Encountered an error with processing the data.", data)

    # return metrics table (list of dictionaries as records of metrics)
    data_table = [
        {
            **metric,
            # add the data results for the metrics to the table
            "result": data[metric["name"]],
        }
        # for each metric, gather the related process data and add to a dictionary
        # related to that metric along with others in a list.
        for metric in metrics_table
    ]

    # calculate almanack score (the function modifies the placeholder)
    return [
        (
            {**entry, "result": compute_almanack_score(almanack_table=data_table)}
            if entry["name"] == "repo-almanack-score"
            else entry
        )
        for entry in data_table
    ]


def file_exists_in_repo(
    repo: pygit2.Repository,
    expected_file_name: str,
    check_extension: bool = False,
    extensions: list[str] = [".md", ""],
) -> bool:
    """
    Check if a file (case-insensitive and with optional extensions)
    exists in the latest commit of the repository.

    Args:
        repo (pygit2.Repository):
            The repository object to search in.
        expected_file_name (str):
            The base file name to check (e.g., "readme").
        check_extension (bool):
            Whether to check the extension of the file or not.
        extensions (list[str]):
            List of possible file extensions to check (e.g., [".md", ""]).

    Returns:
        bool:
            True if the file exists, False otherwise.
    """

    # Gather a tree from the HEAD of the repo
    tree = repo.revparse_single("HEAD").tree

    # Normalize expected file name to lowercase for case-insensitive comparison
    expected_file_name = expected_file_name.lower()

    for entry in tree:
        # Normalize entry name to lowercase
        entry_name = entry.name.lower()

        # Check if the base file name matches with any allowed extension
        if check_extension and any(
            entry_name == f"{expected_file_name}{ext.lower()}" for ext in extensions
        ):
            return True

        # Check whether the filename without an extension matches the expected file name
        if not check_extension and entry_name.split(".", 1)[0] == expected_file_name:
            return True

    return False


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
    if (
        file_content := read_file(
            repo=repo, filepath="readme.md", case_insensitive=True
        )
    ) is not None:
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


def days_of_development(repo: pygit2.Repository) -> float:
    """


    Args:
        repo (pygit2.Repository): Path to the git repository.

    Returns:
        float: The average number of commits per day over the period of time.
    """
    try:
        # Try to get the HEAD commit. If it raises an error, there are no commits.
        repo.revparse_single("HEAD")
    except KeyError:
        # If HEAD doesn't exist (repo is empty), return 0 commits.
        return 0

    # Traverse the commit history and collect commit dates
    commit_dates = [
        datetime.fromtimestamp(commit.commit_time).date()
        for commit in repo.walk(repo.head.target, pygit2.GIT_SORT_TIME)
    ]

    # If no commits, return 0
    if not commit_dates:
        return 0

    # Calculate the number of days between the first and last commit
    # +1 to include the first day
    total_days = (max(commit_dates) - min(commit_dates)).days + 1

    # Return the average commits per day
    return total_days


def includes_common_docs(repo: pygit2.Repository) -> bool:
    """
    Check whether the repo includes common documentation files and directories
    associated with building docsites.

    Args:
        repo (pygit2.Repository):
            The repository object.

    Returns:
        bool:
            True if any common documentation files
            are found, False otherwise.
    """
    # List of common documentation file paths to check for
    common_docs_paths = [
        "docs/mkdocs.yml",
        "docs/conf.py",
        "docs/index.md",
        "docs/index.rst",
        "docs/index.html",
        "docs/readme.md",
        "docs/source/readme.md",
        "docs/source/index.rst",
        "docs/source/index.md",
        "docs/src/readme.md",
        "docs/src/index.rst",
        "docs/src/index.md",
    ]

    # Check each documentation path using the find_file function
    for doc_path in common_docs_paths:
        if find_file(repo=repo, filepath=doc_path) is not None:
            return True  # Return True as soon as we find any of the files

    # otherwise return false as we didn't find documentation
    return False


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


def compute_repo_data(repo_path: str) -> None:
    """
    Computes comprehensive data for a GitHub repository.

    Args:
        repo_path (str): The local path to the Git repository.

    Returns:
        dict: A dictionary containing data key-pairs.
    """
    # Convert repo_path to an absolute path and initialize the repository
    repo_path = pathlib.Path(repo_path).resolve()
    repo = pygit2.Repository(str(repo_path))

    remote_url = get_remote_url(repo=repo)

    # gather data from ecosystems repo api
    remote_repo_data = get_api_data(
        params={"url": remote_url} if remote_url is not None else None
    )

    # gather data from github repo workflows api
    gh_workflows_data = get_github_build_metrics(
        repo_url=remote_url, branch=repo.head.shorthand, max_runs=100
    )

    # gather data on code coverage
    code_coverage = measure_coverage(
        repo=repo, primary_language=remote_repo_data.get("language", None)
    )
    # gather data from ecosystems packages api
    packages_data = get_ecosystems_package_metrics(repo_url=remote_url)

    # Retrieve the list of commits from the repository
    commits = get_commits(repo)
    most_recent_commit = commits[0]
    first_commit = commits[-1]

    # Get a list of files that have been edited between the first and most recent commit
    edited_file_names = get_edited_files(repo, first_commit, most_recent_commit)

    # Calculate the normalized total entropy for the repository
    normalized_total_entropy = calculate_aggregate_entropy(
        repo_path,
        str(first_commit.id),
        str(most_recent_commit.id),
        edited_file_names,
    )

    # Calculate the normalized entropy for the changes between the first and most recent commits
    file_entropy = calculate_normalized_entropy(
        repo_path,
        str(first_commit.id),
        str(most_recent_commit.id),
        edited_file_names,
    )
    # Convert commit times to UTC datetime objects, then format as date strings.
    first_commit_date, most_recent_commit_date = (
        datetime.fromtimestamp(commit.commit_time).date()
        for commit in (first_commit, most_recent_commit)
    )

    # date of last code coverage run
    date_of_last_coverage_run = code_coverage.get("date_of_last_coverage_run", None)
    readme_exists = file_exists_in_repo(
        repo=repo,
        expected_file_name="readme",
    )

    # gather social media metrics
    social_media_metrics = (
        detect_social_media_links(
            content=read_file(repo=repo, filepath="readme.md", case_insensitive=True)
        )
        if readme_exists
        else {}
    )

    # gather doi citation data
    doi_citation_data = find_doi_citation_data(repo=repo)

    # Return the data structure
    return {
        "repo-path": str(repo_path),
        "repo-commits": (commits_count := len(commits)),
        "repo-file-count": count_files(tree=most_recent_commit.tree),
        "repo-commit-time-range": (
            first_commit_date.isoformat(),
            most_recent_commit_date.isoformat(),
        ),
        "repo-days-of-development": (
            days_of_development := (most_recent_commit_date - first_commit_date).days
            + 1
        ),
        "repo-commits-per-day": commits_count / days_of_development,
        "almanack-table-datetime": DATETIME_NOW.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "repo-includes-readme": readme_exists,
        "repo-includes-contributing": file_exists_in_repo(
            repo=repo,
            expected_file_name="contributing",
        ),
        "repo-includes-code-of-conduct": file_exists_in_repo(
            repo=repo,
            expected_file_name="code_of_conduct",
        ),
        "repo-includes-license": file_exists_in_repo(
            repo=repo,
            expected_file_name="license",
        ),
        "repo-is-citable": is_citable(repo=repo),
        "repo-default-branch-not-master": default_branch_is_not_master(repo=repo),
        "repo-includes-common-docs": includes_common_docs(repo=repo),
        "almanack-version": _get_almanack_version(),
        "repo-primary-language": remote_repo_data.get("language", None),
        "repo-primary-license": remote_repo_data.get("license", None),
        "repo-doi": doi_citation_data["doi"],
        "repo-doi-publication-date": (
            doi_citation_data["publication_date"].strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            if doi_citation_data["publication_date"] is not None
            else None
        ),
        # placeholders for almanack score metrics
        "repo-almanack-score": None,
        "repo-unique-contributors": count_unique_contributors(repo=repo),
        "repo-unique-contributors-past-year": count_unique_contributors(
            repo=repo, since=(one_year_ago := DATETIME_NOW - timedelta(days=365))
        ),
        "repo-unique-contributors-past-182-days": count_unique_contributors(
            repo=repo, since=(half_year_ago := DATETIME_NOW - timedelta(days=182))
        ),
        "repo-tags-count": count_repo_tags(repo=repo),
        "repo-tags-count-past-year": count_repo_tags(repo=repo, since=one_year_ago),
        "repo-tags-count-past-182-days": count_repo_tags(
            repo=repo, since=half_year_ago
        ),
        "repo-stargazers-count": remote_repo_data.get("stargazers_count", None),
        "repo-uses-issues": remote_repo_data.get("has_issues", None),
        "repo-issues-open-count": remote_repo_data.get("open_issues_count", None),
        "repo-pull-requests-enabled": remote_repo_data.get(
            "pull_requests_enabled", None
        ),
        "repo-forks-count": remote_repo_data.get("forks_count", None),
        "repo-subscribers-count": remote_repo_data.get("subscribers_count", None),
        "repo-packages-ecosystems": packages_data.get("ecosystems_names", None),
        "repo-packages-ecosystems-count": packages_data.get("ecosystems_count", None),
        "repo-packages-versions-count": packages_data.get("versions_count", None),
        "repo-social-media-platforms": social_media_metrics.get(
            "social_media_platforms", None
        ),
        "repo-social-media-platforms-count": social_media_metrics.get(
            "social_media_platforms_count", None
        ),
        "repo-doi-valid-format": doi_citation_data["valid_format_doi"],
        "repo-doi-https-resolvable": doi_citation_data["https_resolvable_doi"],
        "repo-days-between-doi-publication-date-and-latest-commit": (
            (most_recent_commit_date - doi_citation_data["publication_date"]).days
            if doi_citation_data["publication_date"] is not None
            else None
        ),
        "repo-doi-cited-by-count": doi_citation_data["cited_by_count"],
        "repo-gh-workflow-success-ratio": gh_workflows_data.get("success_ratio", None),
        "repo-gh-workflow-succeeding-runs": gh_workflows_data.get("total_runs", None),
        "repo-gh-workflow-failing-runs": gh_workflows_data.get("successful_runs", None),
        "repo-gh-workflow-queried-total": gh_workflows_data.get("failing_runs", None),
        "repo-code-coverage-percent": code_coverage.get("code_coverage_percent", None),
        "repo-date-of-last-coverage-run": (
            date_of_last_coverage_run.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            if date_of_last_coverage_run is not None
            else None
        ),
        "repo-days-between-last-coverage-run-latest-commit": (
            (most_recent_commit_date - date_of_last_coverage_run).days
            if date_of_last_coverage_run is not None
            else None
        ),
        "repo-code-coverage-total-lines": code_coverage.get("total_lines", None),
        "repo-code-coverage-executed-lines": code_coverage.get("executed_lines", None),
        "repo-agg-info-entropy": normalized_total_entropy,
        "repo-file-info-entropy": file_entropy,
    }


def compute_pr_data(repo_path: str, pr_branch: str, main_branch: str) -> Dict[str, Any]:
    """
    Computes entropy data for a PR compared to the main branch.

    Args:
        repo_path (str): The local path to the Git repository.
        pr_branch (str): The branch name for the PR.
        main_branch (str): The branch name for the main branch.

    Returns:
        dict: A dictionary containing the following key-value pairs:
            - "pr_branch": The PR branch being analyzed.
            - "main_branch": The main branch being compared.
            - "total_entropy_introduced": The total entropy introduced by the PR.
            - "number_of_files_changed": The number of files changed in the PR.
            - "entropy_per_file": A dictionary of entropy values for each changed file.
            - "commits": A tuple containing the most recent commits on the PR and main branches.
    """
    try:
        # Convert repo_path to an absolute path and initialize the repository
        repo_path = pathlib.Path(repo_path).resolve()
        repo = pygit2.Repository(str(repo_path))

        # Get the PR and main branch references
        pr_ref = repo.branches.local.get(pr_branch)
        main_ref = repo.branches.local.get(main_branch)

        # Get the most recent commits on each branch
        pr_commit = repo.get(pr_ref.target)
        main_commit = repo.get(main_ref.target)

        # Get the list of files that have been edited between the two commits
        changed_files = get_edited_files(repo, main_commit, pr_commit)

        # Calculate the total entropy introduced by the PR
        total_entropy_introduced = calculate_aggregate_entropy(
            repo_path,
            str(main_commit.id),
            str(pr_commit.id),
            changed_files,
        )

        # Calculate the entropy for each file changed in the PR
        file_entropy = calculate_normalized_entropy(
            repo_path,
            str(main_commit.id),
            str(pr_commit.id),
            changed_files,
        )

        # Convert commit times to UTC datetime objects, then format as date strings
        pr_commit_date = (
            datetime.fromtimestamp(pr_commit.commit_time, tz=timezone.utc)
            .date()
            .isoformat()
        )
        main_commit_date = (
            datetime.fromtimestamp(main_commit.commit_time, tz=timezone.utc)
            .date()
            .isoformat()
        )

        # Return the data structure
        return {
            "pr_branch": pr_branch,
            "main_branch": main_branch,
            "total_entropy_introduced": total_entropy_introduced,
            "number_of_files_changed": len(changed_files),
            "file_level_entropy": file_entropy,
            "commits": (main_commit_date, pr_commit_date),
        }

    except Exception as e:
        # If processing fails, return an informative error
        return {"pr_branch": pr_branch, "main_branch": main_branch, "error": str(e)}


def process_repo_for_analysis(
    repo_url: str,
) -> Tuple[Optional[float], Optional[str], Optional[str], Optional[int]]:
    """
    Processes GitHub repository URL's to calculate entropy and other metadata.
    This is used to prepare data for analysis, particularly for the seedbank notebook
    that process PUBMED repositories.

    Args:
        repo_url (str): The URL of the GitHub repository.

    Returns:
        tuple: A tuple containing the normalized total entropy, the date of the first commit,
               the date of the most recent commit, and the total time of existence in days.
    """
    temp_dir = tempfile.mkdtemp()
    try:
        repo_path = clone_repository(repo_url)
        # Load the cloned repo
        repo = pygit2.Repository(str(repo_path))

        # Retrieve the list of commits from the repo
        commits = get_commits(repo)
        # Select the first and most recent commits from the list
        first_commit = commits[-1]
        most_recent_commit = commits[0]

        # Calculate the time span of existence between the first and most recent commits in days
        time_of_existence = (
            most_recent_commit.commit_time - first_commit.commit_time
        ) // (24 * 3600)
        # Calculate the time span between commits in days. Using UTC for date conversion ensures uniformity
        # and avoids issues related to different time zones and daylight saving changes.
        first_commit_date = (
            datetime.fromtimestamp(first_commit.commit_time, tz=timezone.utc)
            .date()
            .isoformat()
        )
        most_recent_commit_date = (
            datetime.fromtimestamp(most_recent_commit.commit_time, tz=timezone.utc)
            .date()
            .isoformat()
        )
        # Get a list of all files that have been edited between the commits
        file_names = get_edited_files(repo, commits)
        # Calculate the normalized entropy for the changes between the first and most recent commits
        normalized_total_entropy = calculate_aggregate_entropy(
            repo_path, str(first_commit.id), str(most_recent_commit.id), file_names
        )

        return (
            normalized_total_entropy,
            first_commit_date,
            most_recent_commit_date,
            time_of_existence,
        )

    except Exception as e:
        return (
            None,
            None,
            None,
            None,
            f"An error occurred while processing the repository: {e!s}",
        )

    finally:
        shutil.rmtree(temp_dir)


def _get_almanack_version() -> str:
    """
    Seeks the current version of almanack using either pkg_resources
    or dunamai to determine the current version being used.

    Returns:
        str
            A string representing the version of almanack currently being used.
    """

    try:
        # attempt to gather the development version from dunamai
        # for scenarios where almanack from source is used.
        import dunamai

        return dunamai.Version.from_any_vcs().serialize()
    except (RuntimeError, ModuleNotFoundError):
        # else grab a static version from __init__.py
        # for scenarios where the built/packaged almanack is used.
        import almanack

        return almanack.__version__


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
                    LOGGER.warning("Rate limit exceeded. All retry attempts exhausted.")
                    return {}
            else:
                # Raise other HTTP errors immediately
                LOGGER.warning(f"Unexpected HTTP error: {httpe}")
                return {}
        except requests.RequestException as reqe:
            # Raise other non-HTTP exceptions immediately
            LOGGER.warning(f"Unexpected request error: {reqe}")
            return {}

    LOGGER.warning("All retries failed. Returning an empty response.")
    return {}  # Default return in case all retries fail


def get_github_build_metrics(
    repo_url: str,
    branch: str = "main",
    max_runs: int = 100,
    github_api_endpoint: str = "https://api.github.com/repos",
) -> dict:
    """
    Fetches the success ratio of the latest GitHub Actions build runs for a specified branch.

    Args:
        repo_url (str):
            The full URL of the repository (e.g., 'http://github.com/org/repo').
        branch (str):
            The branch to filter for the workflow runs (default: "main").
        max_runs (int):
            The maximum number of latest workflow runs to analyze.
        github_api_endpoint (str):
            Base API endpoint for GitHub repositories.

    Returns:
        dict:
            The success ratio and details of the analyzed workflow runs.
    """
    # Validate and parse the repository URL
    parsed_url = urlparse(repo_url)
    if parsed_url.netloc != "github.com" or not parsed_url.path:
        return {}

    try:
        # gather the owner and repo name from the parsed url path
        owner, repo_name = parsed_url.path.strip("/").split("/")
    except ValueError:
        return {}

    # Fetch the latest workflow run data using get_api_data
    github_response = get_api_data(
        # Construct the API URL for GitHub Actions runs
        api_endpoint=f"{github_api_endpoint}/{owner}/{repo_name}/actions/runs",
        params={"event": "push", "branch": branch, "per_page": max_runs},
    )

    if github_response.get("workflow_runs"):
        workflow_runs = github_response["workflow_runs"]

        # Count successes and total runs
        total_runs = len(workflow_runs)
        successful_runs = sum(
            1 for run in workflow_runs if run["conclusion"] == "success"
        )

        return {
            "success_ratio": successful_runs / total_runs,
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "failing_runs": total_runs - successful_runs,
        }

    # else we return an empty dictionary
    return {}


def measure_coverage(
    repo: pygit2.Repository, primary_language: Optional[str]
) -> Optional[Dict[str, Any]]:
    """
    Measures code coverage for a given repository.

    Args:
        repo (pygit2.Repository):
            The pygit2 repository object to analyze.
        primary_language (Optional[str]):
            The primary programming language of the repository.

    Returns:
        Optional[dict[str,Any]]:
            Code coverage data or an empty dictionary if unable
            to find code coverage data.
    """

    if primary_language is None:
        return {}

    if primary_language.lower() == "python":
        return parse_python_coverage_data(repo)

    return {}


def parse_python_coverage_data(
    repo: pygit2.Repository,
) -> Optional[Dict[str, Any]]:
    """
    Parses coverage.py data from recognized formats such as JSON, XML, or LCOV.
    See here for more information:
    https://coverage.readthedocs.io/en/latest/cmd.html#cmd-report

    Args:
        repo (pygit2.Repository):
            The pygit2 repository object containing code.

    Returns:
        Optional[Dict[str, Any]]:
            A dictionary with standardized code coverage data or an
            empty dict if no data is found.
    """
    coverage_files = [
        "coverage.json",
        "coverage.xml",
        "coverage.lcov",
    ]
    for coverage_file in coverage_files:
        if (
            coverage_object := find_file(repo=repo, filepath=coverage_file)
        ) is not None:
            file_path = f"{repo.workdir}/{coverage_object.name}"
            total_lines = executed_lines = 0
            timestamp = None

            try:
                if coverage_file.endswith(".json"):
                    # Parse JSON coverage data
                    with open(file_path, "r") as f:
                        coverage_data = json.load(f)

                    # Use the `summary` key directly
                    summary = coverage_data.get("summary", {})
                    total_lines = summary.get("num_statements", 0)
                    executed_lines = summary.get("covered_lines", 0)
                    coverage_percentage = summary.get("percent_covered", 0.0)

                    # Retrieve the timestamp
                    timestamp = datetime.fromisoformat(
                        coverage_data["meta"]["timestamp"]
                    )

                elif coverage_file.endswith(".xml"):
                    # Parse XML coverage data (using defusedxml for safely parsing xml)
                    tree = ET.parse(file_path)
                    root = tree.getroot()

                    # Extract the total lines and executed lines directly from the root element
                    total_lines = int(root.attrib.get("lines-valid", 0))
                    executed_lines = int(root.attrib.get("lines-covered", 0))

                    # parse timestamp in XML attributes
                    timestamp_str = root.attrib.get("timestamp")
                    timestamp = datetime.fromtimestamp(
                        float(timestamp_str)
                        / 1000  # Convert from milliseconds to seconds
                    )

                # lcov files are one of the report types
                # produced by coverage.py
                elif coverage_file.endswith(".lcov"):
                    # Parse LCOV coverage data
                    with open(file_path, "r") as f:
                        for line in f:
                            working_line = line.strip()
                            if working_line.startswith(
                                "DA:"
                            ):  # DA:<line number>,<execution count>
                                _, execution_count = working_line.split(":")[1].split(
                                    ","
                                )
                                total_lines += 1
                                if int(execution_count) > 0:
                                    executed_lines += 1

                    # Determine the latest commit date for the LCOV file
                    timestamp = next(
                        (
                            datetime.fromtimestamp(commit.commit_time)
                            for commit in repo.walk(
                                repo.head.target, pygit2.GIT_SORT_TIME
                            )
                            if coverage_object.name in commit.tree
                        ),
                        None,
                    )

                # Calculate coverage percentage
                coverage_percentage = (
                    (executed_lines / total_lines * 100) if total_lines > 0 else 0.0
                )

                return {
                    "code_coverage_percent": coverage_percentage,
                    "date_of_last_coverage_run": timestamp,
                    "total_lines": total_lines,
                    "executed_lines": executed_lines,
                }

            except Exception as e:
                LOGGER.warning(f"Error reading {coverage_file}: {e}")
                continue

    # No recognized coverage files found
    LOGGER.warning("No coverage.py data found in the repository.")
    return {}


def get_ecosystems_package_metrics(repo_url: str) -> Dict[str, Any]:
    """
    Fetches package data from the ecosystem API and calculates metrics
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
        LOGGER.warning(
            "Did not receive a valid repository URL and unable to gather package metrics."
        )
        return {}

    # normalize http to https if necessary
    if repo_url.startswith("http://"):
        LOGGER.warning(
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

    # perform package srequest
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


def compute_almanack_score(
    almanack_table: List[Dict[str, Union[int, float, bool]]]
) -> Dict[str, Union[int, float]]:
    """
    Computes an Almanack score by counting boolean Almanack
    table metrics to provide a quick summary of software sustainability.

    Args:
        almanack_table (List[Dict[str, Union[int, float, bool]]]):
            A list of dictionaries containing metrics.
            Each dictionary must have a "result" key
            with a value that is an int, float, or bool.
            A "sustainability_correlation" key is
            included for values to specify the
            relationship to sustainability:
            - 1 (positive correlation)
            - 0 (no correlation)
            - -1 (negative correlation)

    Returns:
        Dict[str, Union[int, float]]:
            Dictionary of length three, including the following:
            1) number of Almanack boolean metrics that passed
            (numerator), 2) number of total Almanack boolean
            metrics considered (denominator), and 3) a score that
            represents how likely the repository will be maintained
            over time based (numerator / denominator).
    """

    bool_results = []

    # Gather boolean Almanack values, contingent on sustainability_correlation
    for item in almanack_table:
        # We translate boolean values into numeric values based on the
        # sustainability_correlation provided from the metrics.yml file.
        # We transform the score based on the following logic:
        # - True with sustainability_correlation 1 = 1
        # - True with sustainability_correlation -1 = 0
        # - False with sustainability_correlation 1 = 0
        # - False with sustainability_correlation -1 = 1
        if item["result-type"] == "bool" and item["sustainability_correlation"] != 0:
            # for sustainability_correlation == 1 we treat True as positive sustainability indicator
            # and False as a negative sustainability indicator.
            # note: bools are a subclass of ints in Python.
            if item["sustainability_correlation"] == 1:
                bool_results.append(
                    int(item["result"]) if item["result"] is not None else 0
                )
            # for sustainability_correlation == -1 we treat True as negative sustainability indicator.
            # and False as a positive sustainability indicator.
            # note: bools are a subclass of ints in Python.
            elif item["sustainability_correlation"] == -1:
                bool_results.append(
                    int(not item["result"]) if item["result"] is not None else 0
                )

    almanack_score_values = {
        # capture numerator and denominator for use alongside the almanack score data
        "almanack-score-numerator": sum(bool_results) if bool_results else None,
        "almanack-score-denominator": len(bool_results) if bool_results else None,
        # Calculate almanack score, normalized to between 0 and 1
        "almanack-score": (
            sum(bool_results) / len(bool_results) if bool_results else None
        ),
    }
    return almanack_score_values
