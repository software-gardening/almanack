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


def calculate_loc_changes(
    repo_path: pathlib.Path, source: str, target: str, file_names: list[str]
) -> dict[str, int]:
    """
    Finds the total number of code lines changed for each specified file between two commits.

    Args:
        repo_path (pathlib.Path): The path to the git repository.
        source (str): The source commit hash.
        target (str): The target commit hash.
        file_names (list[str]): List of file names to calculate changes for.

    Returns:
        dict[str, int]: A dictionary where the key is the filename, and the value is the lines changed (added and removed).
    """
    repo = git.Repo(repo_path)
    changes = {}

    for file_name in file_names:
        # Get the diff output for the file between the two commits
        diff_output = repo.git.diff(source, target, "--numstat", "--", file_name)
        # Parse the diff output, then sum the the value of lines added and removed
        lines_changed = sum(
            abs(int(removed)) + int(added)
            for added, removed, _ in (line.split() for line in diff_output.splitlines())
        )
        changes[file_name] = lines_changed
    return changes
