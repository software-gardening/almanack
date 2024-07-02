from test_git_parser import get_most_recent_commits

from almanack.entropy import calculate_shannon_entropy
from almanack.git_parser import *


def test_calculate_entropy(repository_paths: dict[str, pathlib.Path]) -> None:
    file_sets = {
        "high_entropy": ["high_entropy2.md", "high_entropy.md"],
        "low_entropy": ["low_entropy.md"],
    }
    for label, repo_path in repository_paths.items():
        source_commit, target_commit = get_most_recent_commits(repo_path)
        entropies = calculate_shannon_entropy(
            repo_path, source_commit, target_commit, file_sets[label]
        )
        for _, entropy in entropies.items():
            assert entropy >= 0  # Check if entropy is negative
