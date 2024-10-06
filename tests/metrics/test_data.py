"""
Testing generate_data functionality
"""

import pathlib

import pandas as pd

from almanack.metrics.data import compute_repo_data, get_table


def test_generate_repo_data(repository_paths: dict[str, pathlib.Path]) -> None:
    """
    Testing generate_whole_repo_data produces the expected output for given repositories.
    """
    for _, repo_path in repository_paths.items():
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


def test_get_table(repository_paths: dict[str, pathlib.Path]) -> None:
    """
    Tests the almanack.metrics.data.get_table function
    """

    for name, repo_path in repository_paths.items():

        # create a table from the repo
        table = get_table(str(repo_path))

        # check table type
        assert isinstance(table, list)

        # check that the columns appear as expected when forming a dataframe of the output
        assert pd.DataFrame(table).columns.tolist() == [
            "name",
            "id",
            "result-type",
            "description",
            "result",
        ]
