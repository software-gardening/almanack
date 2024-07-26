"""
This module parses Git logs and utilizes commit data to analyze changes
"""

import pathlib
from typing import Dict, List

import git
import pygit2


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
