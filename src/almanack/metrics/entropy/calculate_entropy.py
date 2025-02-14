"""
This module calculates the amount of Software information entropy
"""

import math
import pathlib
from typing import List

import pygit2

from almanack.git import get_loc_changed


def calculate_normalized_entropy(
    repo_path: pathlib.Path,
    source_commit: pygit2.Commit,
    target_commit: pygit2.Commit,
    file_names: list[str],
) -> dict[str, float]:
    """
    Calculates the entropy of changes in specified files between two commits,
    inspired by Shannon's information theory entropy formula.
    Normalized relative to the total lines of code changes across specified files.
    We follow an approach described by Hassan (2009) (see references).

    Application of Entropy Calculation:
    Entropy measures the uncertainty in a given system. Calculating the entropy
    of lines of code (LoC) changed reveals the variability and complexity of
    modifications in each file. Higher entropy values indicate more unpredictable
    changes, helping identify potentially unstable code areas.

    Args:
        repo_path (str): The file path to the git repository.
        source_commit (pygit2.Commit): The git hash of the source commit.
        target_commit (pygit2.Commit): The git hash of the target commit.
        file_names (list[str]): List of file names to calculate entropy for.

    Returns:
        dict[str, float]: A dictionary mapping file names to their calculated entropy.

    References:
        * Hassan, A. E. (2009). Predicting faults using the complexity of code changes.
            2009 IEEE 31st International Conference on Software Engineering, 78-88.
            https://doi.org/10.1109/ICSE.2009.5070510
    """
    loc_changes = get_loc_changed(repo_path, source_commit, target_commit, file_names)
    # Calculate total lines of code changes across all specified files
    total_changes = sum(loc_changes.values())

    # Calculate the entropy for each file, relative to total changes
    entropy_calculation = {
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
    return entropy_calculation


def calculate_aggregate_entropy(
    repo_path: pathlib.Path,
    source_commit: pygit2.Commit,
    target_commit: pygit2.Commit,
    file_names: List[str],
) -> float:
    """
    Computes the aggregated normalized entropy score from the output of
    calculate_normalized_entropy for specified a Git repository.
    Inspired by Shannon's information theory entropy formula.
    We follow an approach described by Hassan (2009) (see references).

    Args:
        repo_path (str): The file path to the git repository.
        source_commit (pygit2.Commit): The git hash of the source commit.
        target_commit (pygit2.Commit): The git hash of the target commit.
        file_names (list[str]): List of file names to calculate entropy for.

    Returns:
        float: Normalized entropy calculation.

    References:
        * Hassan, A. E. (2009). Predicting faults using the complexity of code changes.
            2009 IEEE 31st International Conference on Software Engineering, 78-88.
            https://doi.org/10.1109/ICSE.2009.5070510
    """
    # Get the entropy for each file
    entropy_calculation = calculate_normalized_entropy(
        repo_path, source_commit, target_commit, file_names
    )

    # Calculate total entropy of the repository
    total_entropy = sum(entropy_calculation.values())

    # Normalize total entropy by the number of files edited between the two commits
    num_files = len(file_names)
    normalized_total_entropy = (
        total_entropy / num_files if num_files > 0 else 0.0
    )  # Avoid division by zero (e.g., num_files = 0) and ensure valid entropy calculation
    return normalized_total_entropy
