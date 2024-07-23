"""
This module processes Git repositories
"""

import pathlib
import shutil
import tempfile
from datetime import datetime, timezone

import pygit2

from .entropy import aggregate_entropy_calculation


def process_repository(repo_url: str) -> (float, str, str, int):  # type: ignore
    """
    Processes a GitHub repository URL to calculate entropy and other metadata.

    Args:
        repo_url (str): The URL of the GitHub repository.

    Returns:
        tuple: A tuple containing the normalized total entropy, the date of the first commit,
               the date of the most recent commit, and the total time of existence in days.

    """
    temp_dir = tempfile.mkdtemp()
    try:
        # Clone the repository into the temporary directory
        repo_path = pathlib.Path(temp_dir) / "repo"
        pygit2.clone_repository(repo_url, str(repo_path))

        repo = pygit2.Repository(str(repo_path))

        # Get the list of commits on the main branch
        head = repo.revparse_single("HEAD")
        walker = repo.walk(
            head.id, pygit2.GIT_SORT_NONE
        )  # Use GIT_SORT_NONE to ensure all commits are included
        commits = [commit for commit in walker]

        # Get the first and most recent commits
        first_commit = commits[-1]
        most_recent_commit = commits[0]

        # Calculate the total existence time of the repository in days
        time_of_existence = (
            most_recent_commit.commit_time - first_commit.commit_time
        ) // (24 * 3600)

        # Find the dates of the first and most recent commits
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

        # Find all files that have been edited in the repository
        file_names = set()
        for commit in commits:
            if commit.parents:
                # Get the parent commit to calculate the diff
                parent = commit.parents[0]
                # Generate the diff between the current commit and its parent
                diff = repo.diff(parent, commit)
                # Iterate over each file change (patch) in the diff
                for patch in diff:
                    # Add the old file path to the set if it exists
                    if patch.delta.old_file.path:
                        file_names.add(patch.delta.old_file.path)
                    # Add the new file path to the set if it exists
                    if patch.delta.new_file.path:
                        file_names.add(patch.delta.new_file.path)
        file_names = list(file_names)

        # Calculate the total normalized entropy for the repository
        normalized_total_entropy = aggregate_entropy_calculation(
            repo_path, str(first_commit.id), str(most_recent_commit.id), file_names
        )

        return (
            normalized_total_entropy,
            first_commit_date,
            most_recent_commit_date,
            time_of_existence,
        )

    except Exception:
        # Handle any exceptions by appending a row with None values
        return None, None, None, None

    finally:
        # Clean up temp directory
        shutil.rmtree(temp_dir)
