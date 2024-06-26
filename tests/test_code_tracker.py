"""
Testing LoC_tracker functionality for calculating total lines changed in a given repository.
"""

import pathlib

from almanack.code_tracker import calculate_loc_changes
from almanack.git_parser import get_commit_logs

# def test_calculate_loc_changes(repository_paths: dict[str, pathlib.Path]) -> None:
#     # repository_paths.items() returns a dictionary
#     for _, repo_path in repository_paths.items():
#         # Check that the changes are non-negative for each repository
#         assert calculate_loc_changes(repo_path) > 0


def test_calculate_loc_changes(repository_paths: dict[str, pathlib.Path]) -> None:
    for _, repo_path in repository_paths.items():
        source_commit, target_commit = get_most_recent_commits(repo_path)
        # Calculate lines of code changes between source and target commits
        assert calculate_loc_changes(repo_path, source_commit, target_commit) > 0


def get_most_recent_commits(repo_path: pathlib.Path) -> tuple[str, str]:
    """
    Determine the two most recent commit hashes in the repository.

    Args:
        repo_path (pathlib.Path): The path to the git repository.

    Returns:
        tuple[str, str]: Tuple containing the source and target commit hashes.
    """
    # Implement your logic to determine the two most recent commit hashes
    # Example: Return the commit hashes of the two most recent commits
    commit_logs = get_commit_logs(repo_path)

    # Ensure there are at least two commits
    if len(commit_logs) < 2:
        raise ValueError(
            f"Not enough commits in repository {repo_path} to determine most recent commits"
        )

    # Sort commits by their timestamp to get the two most recent ones
    sorted_commits = sorted(commit_logs.items(), key=lambda item: item[1]["timestamp"])

    # Get the commit hashes of the two most recent commits
    source_commit = sorted_commits[-2][0]
    target_commit = sorted_commits[-1][0]
    print(source_commit)
    print(target_commit)
    return source_commit, target_commit
