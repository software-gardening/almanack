"""
Testing LoC_tracker functionality for calculating total lines changed in a given repository.
"""

import pathlib

from almanack.LoC_tracker import calculate_loc_changes


def test_calculate_loc_changes(repository_paths: dict[str, pathlib.Path]):
    # repository_paths.items() returns a dictionary
    for _, repo_path in repository_paths.items():
        # Check that the changes are non-negative for each repository
        assert calculate_loc_changes(repo_path) > 0
