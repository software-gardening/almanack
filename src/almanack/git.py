"""
This module performs git operations
"""

import pathlib
import tempfile
from typing import Dict, List

import pygit2


def clone_repository(repo_url: str) -> pathlib.Path:
    """
    Clones the GitHub repository to a temporary directory.

    Args:
        repo_url (str): The URL of the GitHub repository.

    Returns:
        pathlib.Path: Path to the cloned repository.
    """
    # Create a temporary directory to store the cloned repository
    temp_dir = tempfile.mkdtemp()
    # Define the path for the cloned repository within the temporary directory
    repo_path = pathlib.Path(temp_dir) / "repo"
    # Clone the repository from the given URL into the defined path
    pygit2.clone_repository(repo_url, str(repo_path))
    return repo_path


def get_commits(repo: pygit2.Repository) -> List[pygit2.Commit]:
    """
    Retrieves the list of commits from the main branch.

    Args:
        repo (pygit2.Repository): The Git repository.

    Returns:
        List[pygit2.Commit]: List of commits in the repository.
    """
    # Get the latest commit (HEAD) from the repository
    head = repo.revparse_single("HEAD")
    # Create a walker to iterate over commits starting from the HEAD
    walker = repo.walk(
        head.id, pygit2.enums.SortMode.NONE
    )  #  SortMode.NONE traverses commits in natural order; no sorting applied.
    # Collect all commits from the walker into a list
    commits = list(walker)
    return commits


def get_edited_files(
    repo: pygit2.Repository,
    source_commit: pygit2.Commit,
    target_commit: pygit2.Commit,
) -> List[str]:
    """
    Finds all files that have been edited, added, or deleted between two specific commits.

    Args:
        repo (pygit2.Repository): The Git repository.
        source_commit (pygit2.Commit): The source commit.
        target_commit (pygit2.Commit): The target commit.

    Returns:
        List[str]: List of file names that have been edited, added, or deleted between the two commits.
    """

    # Create a set to store unique file names that have been edited
    file_names = set()
    # Get the differences (diff) between the source and target commits
    diff = repo.diff(source_commit, target_commit)
    # Iterate through each patch in the diff
    for patch in diff:
        # If the old file path is present, add it to the set
        if patch.delta.old_file.path:
            file_names.add(patch.delta.old_file.path)
        # If the new file path is present, add it to the set
        if patch.delta.new_file.path:
            file_names.add(patch.delta.new_file.path)
    return list(file_names)


def get_loc_changed(
    repo_path: pathlib.Path, source: str, target: str, file_names: List[str]
) -> Dict[str, int]:
    """
    Finds the total number of code lines changed for each specified file between two commits.

    Args:
        repo_path (pathlib.Path): The path to the git repository.
        source (str): The source commit hash.
        target (str): The target commit hash.
        file_names (List[str]): List of file names to calculate changes for.

    Returns:
        Dict[str, int]: A dictionary where the key is the filename, and the value is the lines changed (added and removed).
    """
    repo = pygit2.Repository(str(repo_path))

    # Resolve the source and target commits by their hashes
    source_commit = repo.revparse_single(source)
    target_commit = repo.revparse_single(target)

    changes = {}
    # Compute the diff between the source and target commits
    diff = repo.diff(source_commit, target_commit)

    # Iterate over each patch in the diff
    for patch in diff:
        if patch.delta.new_file.path in file_names:
            additions = 0
            deletions = 0
            # Iterate over each hunk in the patch
            for hunk in patch.hunks:
                # Iterate over each line in the hunk
                for line in hunk.lines:
                    if line.origin == "+":
                        additions += 1
                    elif line.origin == "-":
                        deletions += 1
            lines_changed = additions + deletions
            # Store the number of lines changed for the file
            changes[patch.delta.new_file.path] = lines_changed

    return changes


def get_most_recent_commits(repo_path: pathlib.Path) -> tuple[str, str]:
    """
    Retrieves the two most recent commit hashes in the test repositories

    Args:
        repo_path (pathlib.Path): The path to the git repository.

    Returns:
        tuple[str, str]: Tuple containing the source and target commit hashes.
    """
    repo = pygit2.Repository(str(repo_path))
    commits = get_commits(repo)

    # Assumes that commits are sorted by time, with the most recent first
    source_commit = commits[1]  # Second most recent
    target_commit = commits[0]  # Most recent

    return str(source_commit.id), str(target_commit.id)
