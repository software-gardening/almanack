"""
This module computes data for GitHub Repositories
"""

import pathlib
import shutil
import tempfile
from datetime import datetime, timezone
from typing import Optional, Tuple

import pygit2

from .calculate_entropy import calculate_aggregate_entropy, calculate_normalized_entropy
from .git_operations import clone_repository, get_commits, get_edited_files


def compute_repo_data(repo_path: str) -> None:
    """
    Computes comprehensive data for a GitHub repository.

    Args:
        repo_path (str): The local path to the Git repository.

    Returns:
        dict: A dictionary containing the following key-value pairs:
            - "repo_path": The path of the repository.
            - "total_normalized_entropy": The total normalized entropy calculated for the repository.
            - "number_of_commits": The total number of commits in the repository.
            - "number_of_files": The number of files that have been edited between the first and most recent commit.
            - "time_range_of_commits": A tuple containing the dates of the first and most recent commits.
            - "file_level_entropy": A dictionary of entropy values for each file.
    """
    try:
        # Convert repo_path to an absolute path and initialize the repository
        repo_path = pathlib.Path(repo_path).resolve()
        repo = pygit2.Repository(str(repo_path))

        # Retrieve the list of commits from the repository
        commits = get_commits(repo)
        most_recent_commit = commits[0]
        first_commit = commits[-1]

        # Get a list of files that have been edited between the first and most recent commit
        file_names = get_edited_files(repo, first_commit, most_recent_commit)

        # Calculate the normalized total entropy for the repository
        normalized_total_entropy = calculate_aggregate_entropy(
            repo_path,
            str(first_commit.id),
            str(most_recent_commit.id),
            file_names,
        )

        # Calculate the normalized entropy for the changes between the first and most recent commits
        file_entropy = calculate_normalized_entropy(
            repo_path,
            str(first_commit.id),
            str(most_recent_commit.id),
            file_names,
        )
        # Convert commit times to UTC datetime objects, then format as date strings.
        first_commit_date, most_recent_commit_date = (
            datetime.fromtimestamp(commit.commit_time, tz=timezone.utc)
            .date()
            .isoformat()
            for commit in (first_commit, most_recent_commit)
        )

        # Return the data structure
        return {
            "repo_path": str(repo_path),
            "normalized_total_entropy": normalized_total_entropy,
            "number_of_commits": len(commits),
            "number_of_files": len(file_names),
            "time_range_of_commits": (first_commit_date, most_recent_commit_date),
            "file_level_entropy": file_entropy,
        }

    except Exception as e:
        # If processing fails, return an error dictionary
        return {"repo_path": str(repo_path), "error": str(e)}


from typing import Any, Dict


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
