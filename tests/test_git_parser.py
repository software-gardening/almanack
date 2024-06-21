"""
Testing git_parser functionality for retrieving and collecting Git commit logs and contents.
"""

import pathlib

import git

from almanack.git_parser import (
    collect_all_commit_logs,
    get_commit_contents,
    get_commit_logs,
)


def test_get_commit_logs(repository_paths: dict[str, pathlib.Path]):
    """
    Test get_commit_logs function.
    """
    for repo_path in repository_paths.values():
        commit_logs = get_commit_logs(str(repo_path))
        # Ensure the result is a dictionary
        assert isinstance(commit_logs, dict)
        # Ensure the dictionary is not empty
        assert commit_logs


def test_get_commit_contents(repository_paths: dict[str, pathlib.Path]):
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


def test_collect_all_commit_logs(repository_paths: dict[str, pathlib.Path]):
    """
    Test collect_all_commit_logs function.
    """
    all_logs = collect_all_commit_logs(repository_paths)
    for repo_name in repository_paths:
        # Ensure that logs were collected for each repository
        assert repo_name in all_logs
        # Ensure that the logs for each repository are not empty
        assert all_logs[repo_name]
    print(all_logs)
