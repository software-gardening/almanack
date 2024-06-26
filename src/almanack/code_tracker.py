"""
This module calculates the absolute value of lines of code (LoC) changed (added or removed)
in the given Git repository.
"""

import pathlib

from .git_parser import get_commit_logs

# def calculate_loc_changes(repo_path: pathlib.Path) -> int:
#     """
#     Finds the total number of code lines changed

#     Args:
#         repo_path(str): The path to the git repository
#     Returns:
#         int: Total number of lines added or removed
#     """
#     # Extract commits logs using a function from the git_parser module
#     commit_logs = get_commit_logs(repo_path)

#     # Calculate total lines changed, for each repo, using attributes from `get_commit_logs``
#     total_lines_changed = sum(
#         commit_info["stats"]["total"]["lines"] for commit_info in commit_logs.values()
#     )
#     return total_lines_changed

# def calculate_loc_changes(repo_path: pathlib.Path) -> dict[str, int]:
#     """
#     Finds the total number of code lines changed per file.

#     Args:
#         repo_path (pathlib.Path): The path to the git repository

#     Returns:
#         dict: A dictionary mapping file paths to the total number of lines changed.
#     """
#     commit_logs = get_commit_logs(repo_path)

#     file_changes = {}
#     for commit_info in commit_logs.values():
#         for file_path, file_stats in commit_info["files"].items():
#             if file_path not in file_changes:
#                 file_changes[file_path] = file_stats["total_lines_changed"]
#             else:
#                 file_changes[file_path] += file_stats["total_lines_changed"]
#     print(file_changes)
#     return file_changes


def calculate_loc_changes(repo_path: pathlib.Path, source: str, target: str) -> int:
    """
    Finds the total number of code lines changed between two commits.

    Args:
        repo_path (pathlib.Path): The path to the git repository.
        source (str): The source commit hash.
        target (str): The target commit hash.

    Returns:
        int: Total number of lines added or removed.
    """
    # Extract all commit logs
    commit_logs = get_commit_logs(repo_path)

    # Get the stats for the source and target commits
    source_commit_info = commit_logs[source]
    target_commit_info = commit_logs[target]

    # Calculate total lines changed between the source and target commits
    total_lines_changed = (
        source_commit_info["stats"]["total"]["lines"]
        + target_commit_info["stats"]["total"]["lines"]
    )

    return total_lines_changed
