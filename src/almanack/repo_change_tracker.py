"""
This module calculates the absolute value of lines of code (LoC) changed (added or removed)
in the given Git repository.
"""

import pathlib

from .git_parser import get_commit_logs


def calculate_loc_changes(repo_path: pathlib.Path) -> int:
    """
    Finds the total number of code lines changed

    Args:
        repo_path(str): The path to the git repository
    Returns:
        int: Total number of lines added or removed
    """
    # Extract commits logs using a function from the git_parser module
    commit_logs = get_commit_logs(repo_path)

    # Calculate total lines changed, for each repo, using attributes from `get_commit_logs``
    total_lines_changed = sum(
        commit_info["stats"]["total"]["lines"] for commit_info in commit_logs.values()
    )

    return total_lines_changed
