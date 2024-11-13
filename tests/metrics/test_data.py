"""
Testing metrics/data functionality
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
    default_branch_is_not_master,
    file_exists_in_repo,
    get_table,
    includes_common_docs,
    is_citable,
)
from tests.data.almanack.repo_setup.create_repo import repo_setup


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

        # open the metrics table
        with open(METRICS_TABLE, "r") as f:
            metrics_table = yaml.safe_load(f)

        # check that all keys exist in the output from metrics
        # table to received dict
        assert sorted(data.keys()) == sorted(
            [metric["name"] for metric in metrics_table["metrics"]]
        )

        # Check that repo_path in the output is the same as the input
        assert data["repo-path"] == str(repo_path)


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
                        "description": {"type": "string"},
                    },
                    "required": [
                        "name",
                        "id",
                        "result-type",
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
    community_health_repository_path: pygit2.Repository,
    expected_file_name: str,
    check_extension: bool,
    extensions: List[str],
    expected_result: bool,
):
    """
    Combined test for file_exists_in_repo function using different scenarios.
    """

    result = file_exists_in_repo(
        repo=community_health_repository_path,
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


@pytest.mark.parametrize(
    "files, expected",
    [
        # Test with CITATION.cff
        ({"CITATION.cff": "CITATION content."}, True),
        # Test with CITATION.bib
        ({"CITATION.bib": "CITATION content."}, True),
        # Test citation sections in markdown format
        (
            {"readme.md": "## Citation\nThis is a citation."},
            True,
        ),
        (
            {"readme.md": "## Citing us\n\nHere's our awesome citation."},
            True,
        ),
        # RST scenarios
        ({"README.md": "Citation\n--------"}, True),
        ({"README.md": "Citing\n------"}, True),
        ({"README.md": "Cite\n----"}, True),
        ({"README.md": "How to cite\n-----------"}, True),
        # DOI badge
        (
            {
                "README.md": (
                    "# Awesome project\n\n"
                    "[![DOI](https://img.shields.io/badge/DOI-10.48550/arXiv.2311.13417-blue)]"
                    "(https://doi.org/10.48550/arXiv.2311.13417)"
                ),
            },
            True,
        ),
        ({"README.md": "## How to cite"}, True),
        # Test with README without citation
        (
            {"readme.md": "This is a readme."},
            False,
        ),
        # Test with no citation files
        ({"random.txt": "Some random text."}, False),
        # test the almanack itseft as a special case
        (None, True),
    ],
)
def test_is_citable(tmp_path, files, expected):
    """
    Test if the repository is citable based on various file configurations.
    """

    if files is not None:
        repo = repo_setup(repo_path=tmp_path, files=files)
    else:
        # test the almanack itself
        repo_path = pathlib.Path(".").resolve()
        repo = pygit2.Repository(str(repo_path))

    assert is_citable(repo) == expected


def test_default_branch_is_not_master(tmp_path):
    """
    Tests default_branch_is_not_master
    """

    # create paths for example repos
    # (so they aren't in the same dir and overlapping)
    pathlib.Path((example1 := tmp_path / "example1")).mkdir()
    pathlib.Path((example2 := tmp_path / "example2")).mkdir()
    pathlib.Path((example3 := tmp_path / "example3")).mkdir()
    pathlib.Path((example4 := tmp_path / "example4")).mkdir()
    pathlib.Path((example5 := tmp_path / "example5")).mkdir()

    # test with a master branch
    repo = repo_setup(
        repo_path=example1, files={"example.txt": "example"}, branch_name="master"
    )

    assert not default_branch_is_not_master(repo)

    # test with a main branch
    repo = repo_setup(
        repo_path=example2, files={"example.txt": "example"}, branch_name="main"
    )

    assert default_branch_is_not_master(repo)

    # test with a simulated remote head pointed at remote master
    repo = repo_setup(
        repo_path=example3, files={"example.txt": "example"}, branch_name="main"
    )

    # simulate having a remote head pointed at a branch named master
    repo.create_reference(
        "refs/remotes/origin/master", repo[repo.head.target].id, force=True
    )
    repo.create_reference(
        "refs/remotes/origin/HEAD", "refs/remotes/origin/master", force=True
    )

    # create a local branch which is named something besides master
    repo.create_branch("something_else", repo[repo.head.target])
    repo.set_head("refs/heads/something_else")

    assert not default_branch_is_not_master(repo)

    # test with a simulated remote head pointed at remote main
    repo = repo_setup(
        repo_path=example4, files={"example.txt": "example"}, branch_name="main"
    )

    # simulate having a remote head pointed at a branch named master
    repo.create_reference(
        "refs/remotes/origin/main", repo[repo.head.target].id, force=True
    )
    repo.create_reference(
        "refs/remotes/origin/HEAD", "refs/remotes/origin/main", force=True
    )

    # create a local branch which is named something besides master
    repo.create_branch("something_else", repo[repo.head.target])
    repo.set_head("refs/heads/something_else")

    assert default_branch_is_not_master(repo)

    # test with a simulated remote head pointed at remote main but with local branch master
    repo = repo_setup(
        repo_path=example5, files={"example.txt": "example"}, branch_name="master"
    )

    # simulate having a remote head pointed at a branch named master
    repo.create_reference(
        "refs/remotes/origin/main", repo[repo.head.target].id, force=True
    )
    repo.create_reference(
        "refs/remotes/origin/HEAD", "refs/remotes/origin/main", force=True
    )

    assert not default_branch_is_not_master(repo)


@pytest.mark.parametrize(
    "files, expected_result",
    [
        # Scenario 1: `docs` directory with common documentation files
        (
            {
                "docs/mkdocs.yml": "site_name: Test Docs",
                "docs/index.md": "# Welcome to the documentation",
                "README.md": "# Project Overview",
            },
            True,
        ),
        # Scenario 2: `docs` directory without common documentation files
        (
            {
                "docs/random_file.txt": "This is just a random file",
                "README.md": "# Project Overview",
            },
            False,
        ),
        # Scenario 3: No `docs` directory
        (
            {
                "README.md": "# Project Overview",
                "src/main.py": "# Main script",
            },
            False,
        ),
        # Scenario 4: `docs` directory with misleading names
        (
            {
                "docs/mkdoc.yml": "Not a valid mkdocs file",
                "docs/INDEX.md": "# Not a documentation index",
            },
            False,
        ),
        # Scenario 5: `docs` directory with sphinx-like structure
        (
            {
                "docs/source/index.rst": "An rst index",
            },
            True,
        ),
        # Scenario 6: `docs` directory with sphinx-like structure
        (
            {
                "docs/source/index.md": "An md index",
            },
            True,
        ),
        # Scenario 6: `docs` directory with a readme under source dir
        (
            {
                "docs/source/readme.md": "A readme for nested docs",
            },
            True,
        ),
        # test the almanack itseft as a special case
        (None, True),
    ],
)
def test_includes_common_docs(tmp_path, files, expected_result):
    """
    Tests includes_common_docs
    """
    if files is not None:
        repo = repo_setup(repo_path=tmp_path, files=files)
    else:
        # test the almanack itself
        repo_path = pathlib.Path(".").resolve()
        repo = pygit2.Repository(str(repo_path))

    # Assert that the function returns the expected result
    assert includes_common_docs(repo) == expected_result
