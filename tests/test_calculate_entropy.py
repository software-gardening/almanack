"""
Testing entropy functionality
"""

import pathlib

from test_git_operations import get_most_recent_commits

from almanack.processing.calculate_entropy import (
    calculate_aggregate_entropy,
    calculate_normalized_entropy,
)


def test_calculate_normalized_entropy(
    repository_paths: dict[str, pathlib.Path], repo_file_sets: dict[str, list[str]]
) -> None:
    """
    Test the calculate_normalized_entropy function.
    """
    for label, repo_path in repository_paths.items():
        # Extract two most recent commits: source and target
        source_commit, target_commit = get_most_recent_commits(repo_path)

        # Call calculate_normalized_entropy function
        entropies = calculate_normalized_entropy(
            repo_path, source_commit, target_commit, repo_file_sets[label]
        )

        assert entropies  # Check if the entropies dictionary is not empty

        for entropy in entropies.values():
            assert (
                0 <= entropy <= 1
            )  # Check if entropy is non-negative and within normalized range of [0,1]


def test_calculate_aggregate_entropy(
    repository_paths: dict[str, pathlib.Path], repo_file_sets: dict[str, list[str]]
) -> None:
    """
    Test that calculate_aggregate_entropy function
    """
    repo_entropies = {}

    for label, repo_path in repository_paths.items():
        # Extract two most recent commits: source and target
        source_commit, target_commit = get_most_recent_commits(repo_path)
        # Call calculate_normalized_entropy function
        normalized_entropy = calculate_aggregate_entropy(
            repo_path, source_commit, target_commit, repo_file_sets[label]
        )
        repo_entropies[label] = normalized_entropy

    # Ensure that repositories with different entropy levels have different aggregated scores
    assert repo_entropies["3_file_repo"] > repo_entropies["1_file_repo"]
