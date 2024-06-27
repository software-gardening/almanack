"""
Testing git_parser functionality for retrieving and collecting Git commit logs and contents.
"""

import pathlib

import git

from almanack.git_parser import get_commit_contents, get_commit_logs


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
