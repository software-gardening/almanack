"""
This module calculates the absolute value of lines of code (LoC) changed (added or removed)
in the given Git repository.
"""

import git


def calculate_loc_changes(repo_path: str):
    """
    Finds the total number of code lines changed

    Args:
        repo_path(str): The path to the git repository
    Returns:
        int: Total number of lines added or removed
    """
    repo = git.Repo(repo_path)

    total_lines_changed = 0

    for commit in repo.iter_commits():
        # Retrieve commit statistics
        diff_stat = commit.stats.total
        total_lines_changed += diff_stat["lines"]
    return total_lines_changed
