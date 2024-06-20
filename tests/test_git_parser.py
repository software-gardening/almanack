import pathlib

import git

from almanack.git_parser import (
    collect_all_commit_logs,
    get_commit_contents,
    get_commit_logs,
)


def test_get_commit_logs(repository_paths: dict[str, pathlib.Path]):
    """
    Test the get_commit_logs function to ensure it retrieves commit logs.
    """
    for repo_name, repo_path in repository_paths.items():
        commit_logs = get_commit_logs(str(repo_path))
        assert isinstance(commit_logs, dict), f"{repo_name} logs should be a dictionary"
        assert len(commit_logs) > 0, f"{repo_name} logs should not be empty"


def test_get_commit_contents(repository_paths: dict[str, pathlib.Path]):
    """
    Test the get_commit_contents function to ensure it retrieves commit contents.
    """
    for repo_name, repo_path in repository_paths.items():
        repo = git.Repo(repo_path)
        commit = next(repo.iter_commits(), None)
        if commit:
            commit_contents = get_commit_contents(str(repo_path), commit.hexsha)
            assert isinstance(
                commit_contents, dict
            ), f"{repo_name} commit contents should be a dictionary"


def test_collect_all_commit_logs(repository_paths: str):
    """
    Test the collect_all_commit_logs function to ensure it gathers commit logs
    from both the high_entropy and low_entropy repositories.
    """
    all_logs = collect_all_commit_logs(repository_paths)
    for repo_name in repository_paths.keys():
        assert (
            repo_name in all_logs
        )  # check that the repo names exist as a key in all_logs
        assert len(all_logs[repo_name]) > 0  # Checking if logs are empty
