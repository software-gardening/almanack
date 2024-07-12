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
        Entropy measures the uncertainty in in a given system. Calculating the entropy 
        of lines of code (LoC) changed reveals the variability and complexity of 
        modifications in each file. Higher entropy values indicate more unpredictable 
        changes, helping identify potentially unstable code areas.

    """
    loc_changes = calculate_loc_changes(
        repo_path, source_commit, target_commit, file_names
    )
    # Calculate total lines of code changes across all specified files
    total_changes = sum(loc_changes.values())

    # Calculate the entropy for each file, relative to total changes
    shannon_entropy = {
        file_name: (
            -(
                (loc_changes[file_name] / total_changes)
                * math.log2(
                    loc_changes[file_name] / total_changes
                )  # Entropy Calculation
            )
            if loc_changes[file_name] != 0
            and total_changes
            != 0  # Avoid division by zero and ensure valid entropy calculation
            else 0.0
        )
        for file_name in loc_changes  # Iterate over each file in loc_changes dictionary
    }
    return shannon_entropy
