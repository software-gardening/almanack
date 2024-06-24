"""
This module calculates the absolute value of lines of code (LoC) changed (added or removed)
in the given Git repository.
"""

import git


def calculate_loc_changes(repo_path: str):

    repo = git.Repo(repo_path)

    total_lines_changed = 0

    for commit in repo.iter_commits():
        diff_stat = commit.stats.total
        lines_added = diff_stat["insertions"]
        lines_removed = diff_stat["deletions"]
        total_lines_changed += lines_added + lines_removed
    return total_lines_changed
