"""
Testing metrics/data functionality
"""

import pathlib
from datetime import datetime, timedelta, timezone
from typing import Dict, List

import dunamai
import jsonschema
import pandas as pd
import pygit2
import pytest
import yaml

from almanack.metrics.data import (
    METRICS_TABLE,
    _get_almanack_version,
    compute_repo_data,
    count_unique_contributors,
    default_branch_is_not_master,
    file_exists_in_repo,
    get_table,
    includes_common_docs,
    is_citable,
)
from tests.data.almanack.repo_setup.create_repo import repo_setup

DATETIME_NOW = datetime.now()


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
        ({"files": {"CITATION.cff": "CITATION content."}}, True),
        # Test with CITATION.bib
        ({"files": {"CITATION.bib": "CITATION content."}}, True),
        # Test citation sections in markdown format
        (
            {"files": {"readme.md": "## Citation\nThis is a citation."}},
            True,
        ),
        (
            {"files": {"readme.md": "## Citing us\n\nHere's our awesome citation."}},
            True,
        ),
        # RST scenarios
        ({"files": {"README.md": "Citation\n--------"}}, True),
        ({"files": {"README.md": "Citing\n------"}}, True),
        ({"files": {"README.md": "Cite\n----"}}, True),
        ({"files": {"README.md": "How to cite\n-----------"}}, True),
        # DOI badge
        (
            {
                "files": {
                    "README.md": (
                        "# Awesome project\n\n"
                        "[![DOI](https://img.shields.io/badge/DOI-10.48550/arXiv.2311.13417-blue)]"
                        "(https://doi.org/10.48550/arXiv.2311.13417)"
                    ),
                }
            },
            True,
        ),
        ({"files": {"README.md": "## How to cite"}}, True),
        # Test with README without citation
        (
            {"files": {"readme.md": "This is a readme."}},
            False,
        ),
        # Test with no citation files
        ({"files": {"random.txt": "Some random text."}}, False),
        # test the almanack itseft as a special case
        (None, True),
    ],
)
def test_is_citable(tmp_path, files, expected):
    """
    Test if the repository is citable based on various file configurations.
    """

    if files is not None:
        repo = repo_setup(repo_path=tmp_path, files=[files])
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
        repo_path=example1,
        files=[{"files": {"example.txt": "example"}}],
        branch_name="master",
    )

    assert not default_branch_is_not_master(repo)

    # test with a main branch
    repo = repo_setup(
        repo_path=example2,
        files=[{"files": {"example.txt": "example"}}],
        branch_name="main",
    )

    assert default_branch_is_not_master(repo)

    # test with a simulated remote head pointed at remote master
    repo = repo_setup(
        repo_path=example3,
        files=[{"files": {"example.txt": "example"}}],
        branch_name="main",
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
        repo_path=example4,
        files=[{"files": {"example.txt": "example"}}],
        branch_name="main",
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
        repo_path=example5,
        files=[{"files": {"example.txt": "example"}}],
        branch_name="master",
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
    "files, expected_commits, expected_file_count, expected_days, expected_commits_per_day",
    [
        # Single commit on a single day with one file
        ([{"files": {"file1.txt": "content"}}], 1, 1, 1, 1.0),
        # Two commits on the same day with two files
        (
            [{"files": {"file1.txt": "content"}}, {"files": {"file2.txt": "content"}}],
            2,
            2,
            1,
            2.0,
        ),
        # Multiple commits over multiple days
        (
            [
                {
                    "commit-date": DATETIME_NOW - timedelta(days=2),
                    "files": {"file1.txt": "content"},
                },
                {
                    "commit-date": DATETIME_NOW - timedelta(days=1),
                    "files": {"file2.txt": "content"},
                },
                {"commit-date": DATETIME_NOW, "files": {"file3.txt": "content"}},
            ],
            3,
            3,
            3,
            1.0,
        ),
        # Multiple commits on the same day with multiple files
        (
            [
                {"commit-date": DATETIME_NOW, "files": {"file1.txt": "content"}},
                {"commit-date": DATETIME_NOW, "files": {"file2.txt": "new content"}},
                {
                    "commit-date": DATETIME_NOW,
                    "files": {"file3.txt": "another content"},
                },
            ],
            3,
            3,
            1,
            3.0,
        ),
    ],
)
# add noqa rule below to avoid warnings about too many parameters
def test_commit_frequency_data(  # noqa: PLR0913
    tmp_path: pathlib.Path,
    files: List[Dict[str, str]],
    expected_commits: int,
    expected_file_count: int,
    expected_days: int,
    expected_commits_per_day: float,
):
    """
    Tests to ensure metric keys surrounding commits and commit frequency are
    working as expected.
    """
    # Setup the repository with the provided file structure and dates
    repo_setup(repo_path=tmp_path, files=files)

    # Run the function to compute repo data
    repo_data = compute_repo_data(str(tmp_path))

    # Assertions for repo-commits
    assert (
        repo_data["repo-commits"] == expected_commits
    ), f"Expected {expected_commits} commits, got {repo_data['repo-commits']}"

    # Assertions for repo-file-count
    assert (
        repo_data["repo-file-count"] == expected_file_count
    ), f"Expected {expected_file_count} files, got {repo_data['repo-file-count']}"

    # Assertions for repo-commit-time-range
    if "commit-date" in files[0].keys():
        first_date = files[0]["commit-date"].date().isoformat()
        last_date = files[-1]["commit-date"].date().isoformat()
    else:
        today = DATETIME_NOW.date().isoformat()
        first_date = last_date = today
    assert repo_data["repo-commit-time-range"] == (
        first_date,
        last_date,
    ), f"Expected commit time range ({first_date}, {last_date}), got {repo_data['repo-commit-time-range']}"

    # Assertions for repo-days-of-development
    assert (
        repo_data["repo-days-of-development"] == expected_days
    ), f"Expected {expected_days} days of development, got {repo_data['repo-days-of-development']}"

    # Assertions for repo-commits-per-day
    assert (
        repo_data["repo-commits-per-day"] == expected_commits_per_day
    ), f"Expected {expected_commits_per_day} commits per day, got {repo_data['repo-commits-per-day']}"


@pytest.mark.parametrize(
    "files, expected_result",
    [
        # Scenario 1: `docs` directory with common documentation files
        (
            {
                "files": {
                    "docs/mkdocs.yml": "site_name: Test Docs",
                    "docs/index.md": "# Welcome to the documentation",
                    "README.md": "# Project Overview",
                }
            },
            True,
        ),
        # Scenario 2: `docs` directory without common documentation files
        (
            {
                "files": {
                    "docs/random_file.txt": "This is just a random file",
                    "README.md": "# Project Overview",
                }
            },
            False,
        ),
        # Scenario 3: No `docs` directory
        (
            {
                "files": {
                    "README.md": "# Project Overview",
                    "src/main.py": "# Main script",
                }
            },
            False,
        ),
        # Scenario 4: `docs` directory with misleading names
        (
            {
                "files": {
                    "docs/mkdoc.yml": "Not a valid mkdocs file",
                    "docs/INDEX.md": "# Not a documentation index",
                }
            },
            False,
        ),
        # Scenario 5: `docs` directory with sphinx-like structure
        (
            {
                "files": {
                    "docs/source/index.rst": "An rst index",
                }
            },
            True,
        ),
        # Scenario 6: `docs` directory with sphinx-like structure
        (
            {
                "files": {
                    "docs/source/index.md": "An md index",
                }
            },
            True,
        ),
        # Scenario 6: `docs` directory with a readme under source dir
        (
            {
                "files": {
                    "docs/source/readme.md": "A readme for nested docs",
                }
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
        repo = repo_setup(repo_path=tmp_path, files=[files])
    else:
        # test the almanack itself
        repo_path = pathlib.Path(".").resolve()
        repo = pygit2.Repository(str(repo_path))

    # Assert that the function returns the expected result
    assert includes_common_docs(repo) == expected_result


def test_get_almanack_version():
    """
    Tests _get_almanack_version()
    """

    # compare to the dev version from dunamai as we could only use
    # this test in development.
    assert _get_almanack_version() == dunamai.Version.from_any_vcs().serialize()


@pytest.mark.parametrize(
    "files, since, expected_count",
    [
        # Test case 1: All contributors since the beginning
        (
            [
                {
                    "files": {"file1.txt": "Hello, world!"},
                    "author": {"name": "Alice", "email": "alice@example.com"},
                },
                {
                    "files": {"file2.txt": "Another commit"},
                    "author": {"name": "Bob", "email": "bob@example.com"},
                },
                {
                    "files": {"file3.txt": "Yet another commit"},
                    "author": {"name": "Alice", "email": "alice@example.com"},
                },
            ],
            None,  # since: All contributors
            2,  # Alice and Bob
        ),
        # Test case 2: Contributors in the past 1 year
        (
            [
                {
                    "files": {"file1.txt": "Recent commit"},
                    "commit-date": datetime.now(timezone.utc) - timedelta(days=200),
                    "author": {"name": "Alice", "email": "alice@example.com"},
                },
                {
                    "files": {"file2.txt": "Old commit"},
                    "commit-date": datetime.now(timezone.utc) - timedelta(days=400),
                    "author": {"name": "Bob", "email": "bob@example.com"},
                },
                {
                    "files": {"file3.txt": "Another recent commit"},
                    "commit-date": datetime.now(timezone.utc) - timedelta(days=100),
                    "author": {"name": "Charlie", "email": "charlie@example.com"},
                },
            ],
            datetime.now(timezone.utc) - timedelta(days=365),  # since: 1 year ago
            2,  # Alice and Charlie
        ),
        # Test case 3: Contributors in the past 182 days
        (
            [
                {
                    "files": {"file1.txt": "Recent commit"},
                    "commit-date": datetime.now(timezone.utc) - timedelta(days=150),
                    "author": {"name": "Alice", "email": "alice@example.com"},
                },
                {
                    "files": {"file2.txt": "Older commit"},
                    "commit-date": datetime.now(timezone.utc) - timedelta(days=400),
                    "author": {"name": "Bob", "email": "bob@example.com"},
                },
                {
                    "files": {"file3.txt": "Another recent commit"},
                    "commit-date": datetime.now(timezone.utc) - timedelta(days=50),
                    "author": {"name": "Charlie", "email": "charlie@example.com"},
                },
            ],
            datetime.now(timezone.utc) - timedelta(days=182),  # since: 182 days ago
            2,  # Alice and Charlie
        ),
    ],
)
def test_count_unique_contributors(tmp_path, files, since, expected_count):
    """
    Test the count_unique_contributors function with various time frames and contributors.
    """
    # Set up the repository
    repo_path = tmp_path / "test_repo"
    repo = repo_setup(repo_path, files)

    # Test the count_unique_contributors function
    result = count_unique_contributors(repo, since)

    # Assert the result matches the expected count
    assert result == expected_count, f"Expected {expected_count}, got {result}"
