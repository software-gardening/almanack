"""
Testing generate_data functionality
"""

import pathlib
from typing import List

import jsonschema
import pandas as pd
import pygit2
import pytest
import yaml

from almanack.metrics.data import (
    METRICS_TABLE,
    compute_repo_data,
    file_exists_in_repo,
    get_table,
)


def test_generate_repo_data(entropy_repository_paths: dict[str, pathlib.Path]) -> None:
    """
    Testing generate_whole_repo_data produces the expected output for given repositories.
    """
    for _, repo_path in entropy_repository_paths.items():
        # Call the function
        data = compute_repo_data(str(repo_path))

        # Check that data is not None and it's a dictionary
        assert data is not None
        assert isinstance(data, dict)

        # Check for expected keys
        expected_keys = [
            "repo_path",
            "number_of_commits",
            "number_of_files",
            "time_range_of_commits",
            "readme-included",
            "contributing-included",
            "code-of-conduct-included",
            "license-included",
            "normalized_total_entropy",
            "file_level_entropy",
        ]
        assert all(key in data for key in expected_keys)

        # Check that repo_path in the output is the same as the input
        assert data["repo_path"] == str(repo_path)


def test_get_table(entropy_repository_paths: dict[str, pathlib.Path]) -> None:
    """
    Tests the almanack.metrics.data.get_table function
    """

    for _, repo_path in entropy_repository_paths.items():

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


def test_metrics_yaml():
    """
    Test the metrics yaml for expected results
    """

    # define an expected jsonschema for metrics.yml
    schema = {
        "type": "object",
        "properties": {
            "metrics": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "id": {"type": "string"},
                        "result-type": {"type": "string"},
                        "result-data-key": {"type": "string"},
                        "description": {"type": "string"},
                    },
                    "required": [
                        "name",
                        "id",
                        "result-type",
                        "result-data-key",
                        "description",
                    ],
                },
            }
        },
        "required": ["metrics"],
    }

    # open the metrics table
    with open(METRICS_TABLE, "r") as f:
        metrics_table = yaml.safe_load(f)

    # Validate the structure against the schema
    # (we expect None if all is validated)
    assert jsonschema.validate(instance=metrics_table, schema=schema) is None

    # Check for unique IDs
    ids = [metric["id"] for metric in metrics_table["metrics"]]
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize(
    "expected_file_name, check_extension, extensions, expected_result",
    [
        ("readme", True, [".md", ""], True),
        ("README", False, [], True),
        ("CONTRIBUTING", True, [".md", ""], True),
        ("contributing", False, [], True),
        ("code_of_conduct", True, [".md", ""], True),
        ("CODE_OF_CONDUCT", False, [], True),
        ("LICENSE", True, [".md", ".txt", ""], True),
        ("license", False, [], True),
    ],
)
def test_file_exists_in_repo(
    community_health_repository_path: str,
    expected_file_name: str,
    check_extension: bool,
    extensions: List[str],
    expected_result: bool,
):
    """
    Combined test for file_exists_in_repo function using different scenarios.
    """

    # test a synthetic repo
    repo_path = pathlib.Path(community_health_repository_path).resolve()
    repo = pygit2.Repository(str(repo_path))

    result = file_exists_in_repo(
        repo=repo,
        expected_file_name=expected_file_name,
        check_extension=check_extension,
        extensions=extensions,
    )

    assert result == expected_result

    # test the almanack itself
    repo_path = pathlib.Path(".").resolve()
    repo = pygit2.Repository(str(repo_path))

    result = file_exists_in_repo(
        repo=repo,
        expected_file_name=expected_file_name,
        check_extension=check_extension,
        extensions=extensions,
    )

    assert result == expected_result
