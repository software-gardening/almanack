"""
Testing report.py functionality
"""

import pathlib

from almanack.processing.generate_data import generate_whole_repo_data


def test_process_repo_entropy(repository_paths: dict[str, pathlib.Path]) -> None:
    """
    Testing process_repo_entropy produces the expected JSON output for given repositories.
    """
    for label, repo_path in repository_paths.items():
        # Call the CLI function directly
        json_string = generate_whole_repo_data(str(repo_path))
        assert json_string
        # # Check that the JSON string is not empty
        # assert json_string.strip() != ""
        # # Load the JSON string into a dictionary
        # entropy_data = json.loads(json_string)
        # # Check for expected keys in the JSON output
        # expected_keys = ["repo_path", "total_normalized_entropy"]
        # # Check if all expected keys are present in the entropy_data
        # assert all(key in entropy_data for key in expected_keys)
