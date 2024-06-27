"""
This module calculates the absolute value of lines of code (LoC) changed (added or removed)
between the source and target commit hash.
"""

import pathlib

from .git_parser import get_commit_logs


def calculate_loc_changes(repo_path: pathlib.Path, source: str, target: str) -> int:
    """
    Finds the total number of code lines changed between the source and target commits.

    Args:
        repo_path (pathlib.Path): The path to the git repository.
        source (str): The source commit hash.
        target (str): The target commit hash.
    """
    commit_logs = get_commit_logs(repo_path)

    # Get the stats for the source and target commits
    source_commit_info = commit_logs[source]
    target_commit_info = commit_logs[target]

    # Calculate total lines changed between the source and target commits
    total_lines_changed = (
        source_commit_info["stats"]["total"]["lines"]
        - target_commit_info["stats"]["total"]["lines"]
    )
    print(total_lines_changed)

    return total_lines_changed
