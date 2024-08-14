"""
Testing generate_data functionality
"""

import pathlib

from almanack.processing.compute_data import compute_repo_data


def test_generate_repo_data(repository_paths: dict[str, pathlib.Path]) -> None:
    """
    Testing generate_whole_repo_data produces the expected output for given repositories.
    """
    for label, repo_path in repository_paths.items():
        # Call the function
        data = compute_repo_data(str(repo_path))

        # Check that data is not None and it's a dictionary
        assert data is not None
        assert isinstance(data, dict)

        # Check for expected keys
        expected_keys = [
            "repo_path",
            "normalized_total_entropy",
            "number_of_commits",
            "number_of_files",
            "time_range_of_commits",
            "file_level_entropy",
        ]
        assert all(key in data for key in expected_keys)

        # Check that repo_path in the output is the same as the input
        assert data["repo_path"] == str(repo_path)
