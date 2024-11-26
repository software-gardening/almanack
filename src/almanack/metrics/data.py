"""
This module computes data for GitHub Repositories
"""

import pathlib
import shutil
import tempfile
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import pygit2
import yaml

from ..git import (
    clone_repository,
    count_files,
    find_file,
    get_commits,
    get_edited_files,
    read_file,
)
from .entropy.calculate_entropy import (
    calculate_aggregate_entropy,
    calculate_normalized_entropy,
)

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
    return [
        {
            # remove the result-data-key as this won't be useful to external output
            **{key: val for key, val in metric.items() if key != "result-data-key"},
            # add the data results for the metrics to the table
            "result": data[metric["name"]],
        }
        # for each metric, gather the related process data and add to a dictionary
        # related to that metric along with others in a list.
        for metric in metrics_table
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
        "repo-includes-readme": file_exists_in_repo(
            repo=repo,
            expected_file_name="readme",
        ),
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
