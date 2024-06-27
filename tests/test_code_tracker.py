"""
Testing LoC_tracker functionality for calculating total lines changed in a given repository.
"""

import pathlib

from almanack.code_tracker import calculate_loc_changes
from almanack.git_parser import get_commit_logs

def get_most_recent_commits(repo_path: pathlib.Path) -> tuple[str, str]:
    """
    Determine the two most recent commit hashes in the test repositories.

    Args:
        repo_path (pathlib.Path): The path to the git repository.

    Returns:
        tuple[str, str]: Tuple containing the source and target commit hashes.
    """
    commit_logs = get_commit_logs(repo_path)

    # Sort commits by their timestamp to get the two most recent ones
    sorted_commits = sorted(commit_logs.items(), key=lambda item: item[1]['timestamp'])

    # Get the commit hashes of the two most recent commits
    source_commit = sorted_commits[-2][0]
    target_commit = sorted_commits[-1][0]

    return source_commit, target_commit

def test_calculate_loc_changes(repository_paths: dict[str, pathlib.Path]) -> None:
    for _, repo_path in repository_paths.items():
        source_commit, target_commit = get_most_recent_commits(repo_path)
        # Calculate lines of code changes between source and target commits
        assert calculate_loc_changes(repo_path, source_commit, target_commit) > 0