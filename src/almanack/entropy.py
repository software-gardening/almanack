"""
This module finds the amount of entropy on a file based level
"""

import math

from .git_parser import calculate_loc_changes


def calculate_shannon_entropy(
    repo_path: str, source_commit: str, target_commit: str, file_names: list[str]
) -> dict[str, float]:
    """
    Calculates the Shannon entropy for changes in specified files between two commits.

    Args:
        repo_path (str): The path to the git repository.
        source_commit (str): The hash of the source commit.
        target_commit (str): The hash of the target commit.
        file_names (list[str]): List of file names to calculate entropy for.

    Returns:
        dict[str, float]: A dictionary mapping file names to their calculated entropy.

    """
    changes = calculate_loc_changes(repo_path, source_commit, target_commit, file_names)
    total_changes = sum(changes.values())

    entropy = {}
    for file_name in changes:
        lines_changed = changes[file_name]
        if lines_changed == 0 or total_changes == 0:
            entropy[file_name] = 0.0
        else:
            # Calculate the probability of changes for the current file
            probability = lines_changed / total_changes
            # Calculate the entropy for the current file using the Shannon entropy formula
            entropy[file_name] = -probability * math.log(probability, 2)
    return entropy
