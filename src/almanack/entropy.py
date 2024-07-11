"""
This module finds the amount of entropy on a file based level
"""

import math
import pathlib

from .git_parser import calculate_loc_changes


def calculate_shannon_entropy(
    repo_path: pathlib.Path,
    source_commit: str,
    target_commit: str,
    file_names: list[str],
) -> dict[str, float]:
    """
    Calculates the entropy of changes in specified files between two commits,
    inspired by Shannon's entropy formula.

    Args:
        repo_path (str): The file path to the git repository.
        source_commit (str): The git hash of the source commit.
        target_commit (str): The git hash of the target commit.
        file_names (list[str]): List of file names to calculate entropy for.

    Returns:
        dict[str, float]: A dictionary mapping file names to their calculated entropy.

    Application of Entropy Calculation:
        Entropy measures the uncertainty in changes to the codebase. By calculating
        the entropy of lines of code (LoC) changed, we can find the variability and complexity
        of modifications in each file relative to the entire repository. Higher entropy values indicate
        more unpredictable and substantial changes, which can help identify areas of the code that are
        potentially unstable.

    """
    changes = calculate_loc_changes(repo_path, source_commit, target_commit, file_names)
    total_changes = sum(changes.values())

    shannon_entropy = {}
    for file_name in changes:
        lines_changed = changes[file_name]
        # Checking for 0 values to avoid improper calculation
        if lines_changed == 0 or total_changes == 0:
            shannon_entropy[file_name] = 0.0
        else:
            # Calculate the probability of changes for the current file
            probability = lines_changed / total_changes
            # Calculate the entropy for the current file using the Shannon entropy formula
            shannon_entropy[file_name] = -probability * math.log(probability, 2)
    print(shannon_entropy)
    return shannon_entropy
