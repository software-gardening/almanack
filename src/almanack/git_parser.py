"""
This module parses Git logs and utilizes commit data to analyze changes
"""

import pathlib

import git


def get_commit_logs(repository_path: pathlib.Path) -> dict[str, dict]:
    """
    Retrieves Git logs for a given repository.

    Args:
        repository_path (str): The path to the Git repository.

    Returns:
        dict: A dictionary mapping repository names to dictionaries of commit IDs
              Example: {'repository_name': {'commit_id': {'message': 'Commit message', 'timestamp': 1234567890}}}
    """
    logs = {}
    repo = git.Repo(repository_path)
    for commit in repo.iter_commits():
        logs[commit.hexsha] = {
            "message": commit.message,
            "stats": {"total": {"lines": commit.stats.total["lines"]}},
            "timestamp": commit.authored_date,
            "files": get_commit_contents(repository_path, commit.hexsha),
        }
    return logs


def get_commit_contents(
    repository_path: pathlib.Path, commit_id: pathlib.Path
) -> dict[str, str]:
    """
    Retrieves contents of a specific commit in a Git repository.

    Args:
        repository_path (str): The path to the Git repository.
        commit_id (str): The commit ID to retrieve contents from.

    Returns:
        dict: A dictionary mapping file names to their contents.
              Example: {'filename': 'file_content'}
    """
    contents = {}
    repo = git.Repo(repository_path)
    commit = repo.commit(commit_id)
    contents = {}

    for file_path in commit.tree.traverse():
        contents[file_path.path] = file_path.data_stream.read().decode("utf-8")
    return contents


def calculate_loc_changes(repo_path: pathlib.Path, source: str, target: str) -> int:
    """
    Finds the total number of code lines changed between the source or target commits.

    Args:
        repo_path (pathlib.Path): The path to the git repository.
        source (str): The source commit hash.
        target (str): The target commit hash.
    Returns:
        dict: A dictionary where the key is the filename, and the value is the lines changed (added and removed)
            Example: {'filename': 'change_value'}
    """
    repo = git.Repo(repo_path)
    # diff(--numstat) provides the number of added and removed lines for each file
    diff = repo.git.diff(source, target, "--numstat")
    return {
        filename: abs(int(removed) + int(added))  # Calculate change
        for added, removed, filename in (line.split() for line in diff.splitlines())
    }
