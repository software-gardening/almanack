"""
Testing entropy.py functionality
"""

import pathlib

from test_git_parser import get_most_recent_commits

from almanack.entropy import calculate_shannon_entropy


def test_calculate_shannon_entropy(repository_paths: dict[str, pathlib.Path]) -> None:
    """
    Test calculate_shannon_entropy function.
    """
    file_sets = {
        "test_repo_1": ["file_1.md", "file_2.md", "file_3.md"],
        "test_repo_2": ["file_1.md"],
    }
    for label, repo_path in repository_paths.items():
        source_commit, target_commit = get_most_recent_commits(repo_path)
        entropies = calculate_shannon_entropy(
            repo_path, source_commit, target_commit, file_sets[label]
        )

        for _, entropy in entropies.items():
            assert entropy >= 0  # Check if entropy is negative
