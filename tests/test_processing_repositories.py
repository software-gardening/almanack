"""
Testing processing_repositories.py functionality
"""

import json
import pathlib

from almanack.processing.processing_repositories import process_repo_entropy


def test_process_repo_entropy(repository_paths: dict[str, pathlib.Path]) -> None:
    """
    Testing process_repo_entropy produces the expected JSON output for given repositories.
    """
    for label, repo_path in repository_paths.items():
        # Call the function and get the JSON output
        json_string = process_repo_entropy(str(repo_path))

        # Check that the JSON string is not empty
        assert json_string

        # Load the JSON string into a dictionary
        entropy_data = json.loads(json_string)

        # Check for expected keys in the JSON output
        expected_keys = [
            "repo_path",
            "total_normalized_entropy",
            "number_of_commits",
            "number_of_files",
            "time_range_of_commits",
            "file_level_entropy",
        ]

        # Check if all expected keys are present in the entropy_data
        assert all(key in entropy_data for key in expected_keys)
