"""
Testing git_parser functionality
"""

import pathlib

import git

from almanack.git_parser import (
    calculate_loc_changes,
    get_commit_contents,
    get_commit_logs,
)


def test_get_commit_logs(repository_paths: dict[str, pathlib.Path]) -> None:
    """
    Test get_commit_logs function.
    """
    for repo_path in repository_paths.values():
        commit_logs = get_commit_logs(str(repo_path))
        # Ensure the result is a dictionary
        assert isinstance(commit_logs, dict)
        # Ensure the dictionary is not empty
        assert commit_logs


def test_get_commit_contents(repository_paths: dict[str, pathlib.Path]) -> None:
    """
    Test get_commit_contents function.
    """
    for repo_path in repository_paths.values():
        repo = git.Repo(repo_path)
        # Get the latest commit from the repository
        commit = next(repo.iter_commits(), None)
        # Ensure there is at least one commit in the repository
        assert commit
        commit_contents = get_commit_contents(str(repo_path), commit.hexsha)
        # Ensure the result is a dictionary
        assert isinstance(commit_contents, dict)


def get_most_recent_commits(repo_path: pathlib.Path) -> tuple[str, str]:
    """
    Retrieves the two most recent commit hashes in the test repositories

    Args:
        repo_path (pathlib.Path): The path to the git repository.

    Returns:
        tuple[str, str]: Tuple containing the source and target commit hashes.
    """
    commit_logs = get_commit_logs(repo_path)

    # Sort commits by their timestamp to get the two most recent ones
    sorted_commits = sorted(commit_logs.items(), key=lambda item: item[1]["timestamp"])

    # Get the commit hashes of the two most recent commits
    source_commit = sorted_commits[-2][0]
    target_commit = sorted_commits[-1][0]

    return source_commit, target_commit


def test_calculate_loc_changes(repository_paths: dict[str, pathlib.Path]) -> None:
    """
    Test the calculate_loc_changes function.
    """
    file_sets = {
        "high_entropy": ["high_entropy2.md", "high_entropy.md"],
        "low_entropy": ["low_entropy.md"],
    }

    results = {}

    for label, repo_path in repository_paths.items():
        source_commit, target_commit = get_most_recent_commits(repo_path)
        loc_changes = calculate_loc_changes(
            repo_path, source_commit, target_commit, file_sets[label]
        )
        results[label] = loc_changes
    print(results)
    assert all(
        file_name in loc_changes for file_name in file_sets[label]
    )  # Check that file_sets[label] are present keys
    assert all(
        change >= 0 for change in loc_changes.values()
    )  # Check that all values are non-negative


import math
















def calculate_entropy(repo_path, source_commit, target_commit, file_names):
    changes = calculate_loc_changes(repo_path, source_commit, target_commit, file_names)

    total_changes = sum(changes.values())

    # Calculate entropy for each file
    entropies = {}
    for file_name in file_names:
        lines_changed = changes[file_name]
        probability = lines_changed / total_changes
        # Adjusted entropy calculation to reflect higher entropy for more lines changed
        entropies[file_name] = (-probability * math.log(probability, 2)  )

    return entropies


def test_calculate_entropy(repository_paths: dict[str, pathlib.Path]) -> None:
    file_sets = {
        "high_entropy": ["high_entropy2.md", "high_entropy.md"],
        "low_entropy": ["low_entropy.md"],
    }

    entropy_results = {}

    for label, repo_path in repository_paths.items():
        source_commit, target_commit = get_most_recent_commits(repo_path)
        entropies = calculate_entropy(
            repo_path, source_commit, target_commit, file_sets[label]
        )

        for file_name, entropy in entropies.items():
            if file_name not in entropy_results:
                entropy_results[file_name] = {}
            entropy_results[file_name][label] = entropy

    for file_name, entropies in entropy_results.items():
        print(f"Entropy for {file_name}:")
        for label, entropy in entropies.items():
            print(f"- {label}: {entropy:.2f}")

        # Example assertions if needed
        assert (
            file_name in file_sets[label]
        ), f"{file_name} not in expected file set {file_sets[label]}"
