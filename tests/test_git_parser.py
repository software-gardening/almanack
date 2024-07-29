"""
Testing git_parser functionality
"""

import pathlib

import git

from almanack.git_parser import (
    calculate_loc_changes,
    get_commit_contents,
    get_commit_logs,
)


def test_get_commit_logs(repository_paths: dict[str, pathlib.Path]) -> None:
    """
    Test get_commit_logs function.
    """
    for repo_path in repository_paths.values():
        commit_logs = get_commit_logs(str(repo_path))
        # Ensure the result is a dictionary
        assert isinstance(commit_logs, dict)
        # Ensure the dictionary is not empty
        assert commit_logs


def test_get_commit_contents(repository_paths: dict[str, pathlib.Path]) -> None:
    """
    Test get_commit_contents function.
    """
    for repo_path in repository_paths.values():
        repo = git.Repo(repo_path)
        # Get the latest commit from the repository
        commit = next(repo.iter_commits(), None)
        # Ensure there is at least one commit in the repository
        assert commit
        commit_contents = get_commit_contents(str(repo_path), commit.hexsha)
        # Ensure the result is a dictionary
        assert isinstance(commit_contents, dict)


def get_most_recent_commits(repo_path: pathlib.Path) -> tuple[str, str]:
    """
    Retrieves the two most recent commit hashes in the test repositories

    Args:
        repo_path (pathlib.Path): The path to the git repository.

    Returns:
        tuple[str, str]: Tuple containing the source and target commit hashes.
    """
    commit_logs = get_commit_logs(repo_path)

    # Sort commits by their timestamp to get the two most recent ones
    sorted_commits = sorted(commit_logs.items(), key=lambda item: item[1]["timestamp"])

    # Get the commit hashes of the two most recent commits
    source_commit = sorted_commits[-2][0]
    target_commit = sorted_commits[-1][0]

    return source_commit, target_commit


def test_calculate_loc_changes(
    repository_paths: dict[str, pathlib.Path], repo_file_sets: dict[str, list[str]]
) -> None:
    """
    Test the calculate_loc_changes function.
    """

    results = {}

    for label, repo_path in repository_paths.items():
        # Extract two most recent commits: source and target
        source_commit, target_commit = get_most_recent_commits(repo_path)
        # Call loc_changes function on test repositories
        loc_changes = calculate_loc_changes(
            repo_path, source_commit, target_commit, repo_file_sets[label]
        )
        results[label] = loc_changes
    assert all(
        file_name in loc_changes for file_name in repo_file_sets[label]
    )  # Check that file_sets[label] are present keys
    assert all(
        change >= 0 for change in loc_changes.values()
    )  # Check that all values are non-negative
