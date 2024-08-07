"""
Testing generate_data functionality
"""

import pathlib

from almanack.processing.generate_data import generate_whole_repo_data


def test_process_repo_entropy(repository_paths: dict[str, pathlib.Path]) -> None:
    """
    Testing process_repo_entropy produces the expected JSON output for given repositories.
    """
    for label, repo_path in repository_paths.items():
        # Call the function directly and get the dictionary
        entropy_data = generate_whole_repo_data(str(repo_path))

        # Check that the returned data is a dictionary
        assert isinstance(entropy_data, dict)

        # Check for expected keys in the output
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
