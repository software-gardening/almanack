"""
Testing entropy.py functionality
"""

import pathlib

from test_git_parser import get_most_recent_commits

from almanack.entropy import calculate_normalized_entropy


def test_calculate_shannon_entropy(
    repository_paths: dict[str, pathlib.Path], file_sets: dict[str, list[str]]
) -> None:
    """
    Test calculate_shannon_entropy function.
    """

    for label, repo_path in repository_paths.items():
        # Extract two most recent commits: source and target
        source_commit, target_commit = get_most_recent_commits(repo_path)
        # Call shannon_entropy function on test repositories
        entropies = calculate_normalized_entropy(
            repo_path, source_commit, target_commit, file_sets[label]
        )

        assert entropies  # Check if the entropies dictionary is not empty

        for _, entropy in entropies.items():
            assert entropy >= 0  # Check if entropy is non-negative
        # if label == "test_repo_1":
        #     # Ensure file_2.md has higher entropy than file_1.md and file_3.md
        #     assert (
        #         entropies["file_2.md"] > entropies["file_1.md"]
        #         and entropies["file_2.md"] > entropies["file_3.md"]
        #     )