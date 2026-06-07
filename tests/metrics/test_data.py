"""
Testing metrics/data functionality
"""

import builtins
import pathlib
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Union

import dunamai
import jsonschema
import pandas as pd
import pygit2
import pytest
import requests
import yaml

from almanack.git import find_file, get_remote_url
from almanack.metrics import data as data_module
from almanack.metrics.data import (
    _FALLBACK_PROGRAMMING_EXTENSIONS,
    METRICS_TABLE,
    _get_almanack_version,
    _get_cli_entrypoints,
    _get_conda_python_version,
    _get_programming_extensions,
    _get_pyproject_python_version,
    _get_repository_languages_data,
    _get_software_description,
    _parse_setup_py_console_scripts,
    _walk_tree_measure_size_of_noncode_files,
    compute_almanack_score,
    compute_repo_data,
    gather_failed_almanack_metric_checks,
    get_api_data,
    get_github_build_metrics,
    get_table,
    is_conda_environment_yaml,
    measure_coverage,
)
from almanack.metrics.garden_lattice.connectedness import (
    count_unique_contributors,
    default_branch_is_not_master,
    find_doi_citation_data,
    is_citable,
)
from almanack.metrics.garden_lattice.practicality import (
    count_repo_tags,
    get_ecosystems_package_metrics,
)
from almanack.metrics.garden_lattice.understanding import includes_common_docs
from almanack.metrics.remote import request_with_backoff
from tests.data.almanack.repo_setup.create_repo import repo_setup

DATETIME_NOW = datetime.now()


def test_generate_repo_data(entropy_repository_paths: dict[str, pathlib.Path]) -> None:
    """
    Testing generate_whole_repo_data produces the expected output for given repositories.
    """

    # create a copy of the paths to check so we don't mess with the
    # session-based entropy_repository_paths
    paths_to_check = entropy_repository_paths.copy()

    # add a remote path for the almanack
    paths_to_check["remote"] = "https://github.com/software-gardening/almanack"

    for _, repo_path in paths_to_check.items():
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
        # (so long as we know the path is consistent and not "temp",
        # as it would be for an http link to a repo).
        if not str(repo_path).startswith("http"):
            assert data["repo-path"] == str(repo_path)


@pytest.mark.parametrize(
    "repo_files",
    [
        [
            {
                "files": {
                    "README.md": "# Sample Repo",
                    "CONTRIBUTING.md": "Contribution guidelines",
                },
                "commit-date": datetime(2018, 1, 1),
                "author": {"name": "Author One", "email": "author1@example.com"},
            },
            {
                "files": {
                    "CODE_OF_CONDUCT.md": "Code of conduct",
                    "LICENSE": "MIT License",
                },
                "commit-date": datetime(2021, 1, 2),
                "author": {"name": "Author Two", "email": "author2@example.com"},
            },
        ],
        [
            {
                "files": {
                    "README.txt": "Sample Repo in text format",
                },
                "commit-date": datetime(2023, 1, 1),
                "author": {"name": "Author One", "email": "author1@example.com"},
                "tag": "v3.0.0",
            },
        ],
        [
            {
                "files": {
                    "docs/index.rst": "Documentation index",
                },
                "commit-date": datetime(2024, 1, 1),
                "author": {"name": "author@example.io", "email": "anauthor"},
                "tag": "2024",
            },
        ],
        [
            {
                "files": {
                    "readme.rst": "Read me",
                },
                "commit-date": datetime(2024, 8, 1),
                "author": {"name": "author", "email": "author@example3.edu"},
            },
            {
                "files": {
                    "readme.rst": "Read me",
                },
                "commit-date": datetime(2024, 9, 2),
                "tag": "atag",
            },
        ],
        [
            {
                "files": {
                    "readme.rst": "Read me",
                    # test example of real DOI from Pycytominer paper
                    "CITATION.cff": "doi: 10.1038/s41592-025-02611-8",
                },
                "commit-date": datetime(2024, 8, 1),
                "author": {"name": "author", "email": "author@example3.edu"},
            },
        ],
    ],
)
def test_get_table(repo_files, tmp_path: pathlib.Path) -> None:
    """
    Tests the almanack.metrics.data.get_table function
    """

    # Set up the repository with the provided files
    repo_path = tmp_path / "test_repo"
    repo_setup(repo_path=repo_path, files=repo_files)

    # Create a table from the repo
    table = get_table(repo_path=str(repo_path))

    # Check table type
    assert isinstance(table, list)

    # check that the columns appear as expected when forming a dataframe of the output
    assert pd.DataFrame(table).columns.tolist() == [
        "name",
        "id",
        "result-type",
        "sustainability_correlation",
        "description",
        "correction_guidance",
        "fix_why",
        "fix_how",
        "result",
    ]

    # Check types for the results
    for record in table:
        assert (
            isinstance(record["result"], getattr(builtins, record["result-type"]))
            or record["result"] is None
        ), f"Result from {record['name']} as value {record['result']} is not of type {record['result-type']}."

    # check ignores
    table_with_ignore = get_table(repo_path=str(repo_path), ignore=["SGA-GL-0002"])

    assert len(table_with_ignore) == len(table) - 1

    # check erroneous ignores (should raise an exception)
    with pytest.raises(ValueError) as value_exc:
        get_table(
            repo_path=str(repo_path), ignore=["SGA-GL-NONEXISTENT", "SGA-GL-0002"]
        )
        assert "SGA-GL-NONEXISTENT" in str(value_exc.value)
        assert "SGA-GL-0002" not in str(value_exc.value)


def test_get_table_passes_required_metric_names(
    monkeypatch, tmp_path: pathlib.Path
) -> None:
    """Test that get_table forwards only non-ignored metric names to data capture."""
    with open(METRICS_TABLE, "r") as f:
        metrics_table = yaml.safe_load(f)["metrics"]
    all_metric_names = {metric["name"] for metric in metrics_table}
    ignored_ids = {"SGA-GL-0002", "SGA-GL-0025"}
    expected_required_names = {
        metric["name"] for metric in metrics_table if metric["id"] not in ignored_ids
    }

    captured_required_names = {}

    def _fake_compute_repo_data(
        repo_path, exclude_paths=None, required_metric_names=None
    ):
        _ = repo_path, exclude_paths
        captured_required_names["value"] = required_metric_names
        return {name: None for name in all_metric_names}

    monkeypatch.setattr(data_module, "compute_repo_data", _fake_compute_repo_data)

    get_table(repo_path=str(tmp_path), ignore=list(ignored_ids))

    assert captured_required_names["value"] == expected_required_names


def test_compute_repo_data_skips_entropy_collection_when_not_required(
    tmp_path: pathlib.Path, monkeypatch
) -> None:
    """Test that entropy collection is skipped when entropy metrics are not requested."""
    repo_setup(
        repo_path=tmp_path,
        files=[
            {"files": {"README.md": "initial\n"}, "commit-date": datetime(2024, 1, 1)},
            {
                "files": {"README.md": "initial\nnext\n"},
                "commit-date": datetime(2024, 1, 2),
            },
        ],
    )

    def _raise_if_called(*_):
        raise AssertionError("Entropy collection function should not be called.")

    monkeypatch.setattr(data_module, "get_edited_files", _raise_if_called)
    monkeypatch.setattr(data_module, "calculate_aggregate_entropy", _raise_if_called)
    monkeypatch.setattr(data_module, "calculate_normalized_entropy", _raise_if_called)
    monkeypatch.setattr(
        data_module, "calculate_history_complexity_with_decay", _raise_if_called
    )

    repo_data = compute_repo_data(
        str(tmp_path),
        required_metric_names={"repo-path"},
    )

    assert repo_data["repo-agg-info-entropy"] is None
    assert repo_data["repo-file-info-entropy"] is None
    assert repo_data["repo-agg-history-complexity-decay"] is None
    assert repo_data["repo-file-history-complexity-decay"] is None
    assert repo_data["repo-funding-details"]["doi_work_funding_records_count"] is None
    assert (
        repo_data["repo-funding-details-of-citing-works"][
            "citing_works_funding_records_count_sampled"
        ]
        is None
    )
    assert repo_data["repo-funding-count"] is None
    assert repo_data["repo-funding-count-of-citing-works"] is None
    assert repo_data["repo-funding-amount-usd"] is None
    assert repo_data["repo-funding-amount-usd-of-citing-works"] is None
    assert repo_data["repo-funding-amount-usd-combined"] is None
    assert repo_data["repo-funder-references-count"] is None
    assert repo_data["repo-funder-references-count-of-citing-works"] is None
    assert repo_data["repo-funder-references-count-combined"] is None
    assert repo_data["repo-unique-funders-count"] is None
    assert repo_data["repo-unique-funders-count-of-citing-works"] is None
    assert repo_data["repo-unique-funders-count-combined"] is None
    assert repo_data["repo-check-notebook-exec-order"] is None


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
                        "sustainability_correlation": {
                            "type": "integer",
                            "enum": [1, -1, 0],
                        },
                        "description": {"type": "string"},
                        "correction_guidance": {
                            "anyOf": [{"type": "string"}, {"type": "null"}]
                        },
                        "fix_why": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                        "fix_how": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    },
                    "required": [
                        "name",
                        "id",
                        "result-type",
                        "sustainability_correlation",
                        "description",
                        "correction_guidance",
                        "fix_why",
                        "fix_how",
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
        # test an rst file
        ({"files": {"README.rst": "## How to cite"}}, True),
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
                    "README.rst": "# Project Overview",
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


@pytest.mark.parametrize(
    "files, since, expected_tag_count",
    [
        # No tags in the repository
        (
            [
                {"files": {"file1.txt": "Initial content"}},
                {"files": {"file2.txt": "Another content"}},
            ],
            None,
            0,
        ),
        # One tag in the repository, no since filter
        (
            [
                {"files": {"file1.txt": "Initial content"}, "tag": "v1.0"},
                {"files": {"file2.txt": "Another content"}},
            ],
            None,
            1,
        ),
        # Multiple tags in the repository, no since filter
        (
            [
                {"files": {"file1.txt": "Initial content"}, "tag": "v1.0"},
                {"files": {"file2.txt": "More content"}, "tag": "v1.1"},
                {"files": {"file3.txt": "Even more content"}, "tag": "v2.0"},
            ],
            None,
            3,
        ),
        # Filter by datetime: Only recent tags count
        (
            [
                {
                    "files": {"file1.txt": "Initial content"},
                    "tag": "v1.0",
                    "commit-date": datetime.now() - timedelta(days=10),
                },
                {
                    "files": {"file2.txt": "More content"},
                    "tag": "v1.1",
                    "commit-date": datetime.now() - timedelta(days=5),
                },
                {
                    "files": {"file3.txt": "Even more content"},
                    "tag": "v2.0",
                    "commit-date": datetime.now() - timedelta(days=1),
                },
            ],
            datetime.now() - timedelta(days=7),  # Only tags from the last 7 days
            2,
        ),
    ],
)
def test_count_repo_tags(tmp_path, files, since, expected_tag_count):
    """
    Test count_repo_tags with optional since parameter.
    """
    repo = repo_setup(repo_path=tmp_path, files=files)

    # Assert the tag count matches the expected value
    assert count_repo_tags(repo, since=since) == expected_tag_count


def test_get_api_data(current_repo):
    """
    Test get_api_data using the current repository's remote URL.
    """
    # Get the remote URL of the current repository
    remote_url = get_remote_url(current_repo)
    assert (
        remote_url is not None
    ), "Remote URL could not be determined for the repository."

    # Fetch repository metadata
    repo_data = get_api_data(params={"url": remote_url})

    # Assertions to verify the response
    assert isinstance(repo_data, dict), "The returned repo_data should be a dictionary."
    assert "id" in repo_data, "repo_data should contain the 'name' key."
    assert "full_name" in repo_data, "repo_data should contain the 'url' key."
    assert (
        repo_data["html_url"] == remote_url
    ), "The repo_data URL should match the repository's remote URL."


def test_get_github_build_metrics():
    """
    Tests get_github_build_metrics
    """

    # perform a query against the upstream almanack repo
    result = get_github_build_metrics(
        repo_url="https://github.com/software-gardening/almanack",
        branch="main",
        max_runs=100,
    )

    # check the types for the results (actual values may vary)
    assert isinstance(result["success_ratio"], float)
    assert isinstance(result["total_runs"], int)
    assert isinstance(result["successful_runs"], int)
    assert isinstance(result["failing_runs"], int)


@pytest.mark.parametrize(
    "repo_or_path, primary_language, local_file",
    [
        # tests local case (python coverage.xml)
        (None, "Python", None),
        # test python coverage.json
        ("repo", "Python", "tests/data/almanack/coverage/python/coverage.json"),
        ("repo", "Python", "tests/data/almanack/coverage/python/coverage.lcov"),
    ],
)
def test_measure_coverage(tmp_path, repo_or_path, primary_language, local_file):
    """
    Test measure_coverage with parameterized inputs for local files and repos.
    """

    if repo_or_path is None:
        # test the almanack itself
        repo_path = pathlib.Path(".").resolve()
        repo = pygit2.Repository(str(repo_path))
    else:
        # read the local file
        with open(file=local_file, mode="r") as file:
            file_contents = "\n".join(file.readlines())
        repo = repo_setup(
            repo_path=tmp_path,
            files=[{"files": {pathlib.Path(local_file).name: file_contents}}],
        )

    # Run the test function
    coverage_metrics = measure_coverage(repo=repo, primary_language=primary_language)

    # Assert that the result matches the expected outcome
    assert isinstance(coverage_metrics["code_coverage_percent"], float)
    assert isinstance(coverage_metrics["date_of_last_coverage_run"], datetime)
    assert isinstance(coverage_metrics["total_lines"], int)
    assert isinstance(coverage_metrics["executed_lines"], int)


def test_get_ecosystems_package_metrics():
    """
    Tests get_ecosystems_package_metrics
    """

    # perform a query against the upstream almanack repo
    https_result = get_ecosystems_package_metrics(
        repo_url="https://github.com/software-gardening/almanack",
    )

    # check the types for the results (actual values may vary)
    assert isinstance(https_result["versions_count"], int)
    assert isinstance(https_result["ecosystems_count"], int)
    assert isinstance(https_result["ecosystems_names"], list)

    # check that http and https results are the same
    http_result = get_ecosystems_package_metrics(
        repo_url="http://github.com/software-gardening/almanack",
    )

    assert https_result == http_result

    # check that git@github.com ssh and https results are the same
    git_result = get_ecosystems_package_metrics(
        repo_url="git@github.com:software-gardening/almanack.git",
    )

    assert https_result == git_result


@pytest.mark.parametrize(
    "files_data, expected_result",
    [
        (
            [{"files": {"CITATION.cff": """
                    doi: "10.48550/arXiv.2311.13417"
                    """}}],
            {
                "doi": "10.48550/arXiv.2311.13417",
                "valid_format_doi": True,
                "https_resolvable_doi": True,
                "publication_date": date(2023, 11, 22),
                "cited_by_count": 4,
            },
        ),
        (
            [{"files": {"CITATION.cff": """
                    identifiers:
                        - type: doi
                          value: "10.1186/s44330-024-00014-3"
                    """}}],
            {
                "doi": "10.1186/s44330-024-00014-3",
                "valid_format_doi": True,
                "https_resolvable_doi": True,
                "publication_date": date(2024, 12, 8),
                "cited_by_count": 0,
            },
        ),
        (
            None,
            {
                "doi": "10.5281/zenodo.14765834",
                "valid_format_doi": True,
                "https_resolvable_doi": True,
                "publication_date": date(2025, 2, 10),
                "cited_by_count": 1,
            },
        ),
    ],
)
def test_find_doi_citation_data(tmp_path, files_data, expected_result):
    """
    Tests find_doi_citation_data

    Args:
        tmp_path: Pytest temporary path fixture.
        files_data: Repository files to seed for the test.
        expected_result: Expected DOI metadata output.
    """
    # Setup repository
    if files_data is None:
        # test the almanack itself
        repo_path = pathlib.Path(".").resolve()
        repo = pygit2.Repository(str(repo_path))
    else:
        repo = repo_setup(
            repo_path=tmp_path,
            files=files_data,
        )

    # Skip if DOI endpoint is unavailable to avoid false negatives.
    doi = expected_result.get("doi")
    if doi:
        response = request_with_backoff(
            "HEAD",
            f"https://doi.org/{doi}",
            headers={"accept": "application/json"},
            timeout=30,
            allow_redirects=True,
            max_retries=3,
            base_backoff=1,
            backoff_multiplier=2,
        )
        if response is None or response.status_code != 200:
            pytest.skip(f"DOI endpoint unavailable for {doi}")

    # Run the function
    result = find_doi_citation_data(repo)

    # Assertions to check if the returned data matches the expected result
    assert result["doi"] == expected_result["doi"]
    assert result["valid_format_doi"] == expected_result["valid_format_doi"]
    assert result["https_resolvable_doi"] == expected_result["https_resolvable_doi"]
    assert result["publication_date"] == expected_result["publication_date"]
    assert isinstance(result["cited_by_count"], type(expected_result["cited_by_count"]))


@pytest.mark.parametrize(
    "almanack_table_data, expected",
    [
        # Test case 1: Positive correlation with boolean values
        (
            [
                {
                    "result-type": "bool",
                    "result": True,
                    "sustainability_correlation": 1,
                },
                {
                    "result-type": "bool",
                    "result": False,
                    "sustainability_correlation": 1,
                },
                {
                    "result-type": "bool",
                    "result": True,
                    "sustainability_correlation": 1,
                },
            ],
            {
                "almanack-score-numerator": 2,
                "almanack-score-denominator": 3,
                # Two "True" values contribute 1 each, one "False" contributes 0
                "almanack-score": 0.6666666666666666,
            },
        ),
        # Test case 2: Negative correlation with boolean values
        (
            [
                {
                    "result-type": "bool",
                    "result": True,
                    "sustainability_correlation": -1,
                },
                {
                    "result-type": "bool",
                    "result": False,
                    "sustainability_correlation": -1,
                },
                {
                    "result-type": "bool",
                    "result": True,
                    "sustainability_correlation": -1,
                },
            ],
            (
                {
                    "almanack-score-numerator": 1,
                    "almanack-score-denominator": 3,
                    # Two "True" values contribute 0 each, one "False" contributes 1
                    "almanack-score": 0.3333333333333333,
                }
            ),
        ),
        # Test case 3: Mixed correlation with boolean values
        (
            [
                {
                    "result-type": "bool",
                    "result": True,
                    "sustainability_correlation": 1,
                },
                {
                    "result-type": "bool",
                    "result": False,
                    "sustainability_correlation": -1,
                },
            ],
            {
                "almanack-score-numerator": 2,
                "almanack-score-denominator": 2,
                # One "True" with positive correlation contributes 1, one "False" with negative correlation contributes 1
                "almanack-score": 1.0,
            },
        ),
        # Test case 4: Single boolean value with positive correlation
        (
            [
                {
                    "result-type": "bool",
                    "result": True,
                    "sustainability_correlation": 1,
                },
            ],
            {
                "almanack-score-numerator": 1,
                "almanack-score-denominator": 1,
                "almanack-score": 1.0,
            },  # Single "True" value with positive correlation contributes 1
        ),
        # Test case 5: Single boolean value with negative correlation
        (
            [
                {
                    "result-type": "bool",
                    "result": False,
                    "sustainability_correlation": -1,
                },
            ],
            {
                "almanack-score-numerator": 1,
                "almanack-score-denominator": 1,
                # Single "False" value with negative correlation contributes 1
                "almanack-score": 1.0,
            },
        ),
        # Test case 6: Single boolean value with positive correlation and a numeric metric
        (
            [
                {
                    "result-type": "bool",
                    "result": True,
                    "sustainability_correlation": 1,
                },
                {
                    "result-type": "float",
                    "result": 0.77,
                    "sustainability_correlation": 0,
                },
            ],
            {
                "almanack-score-numerator": 1,
                "almanack-score-denominator": 1,
                "almanack-score": 1.0,
            },
        ),
        # Test case 7: No valid metrics
        (
            [],
            {
                "almanack-score-numerator": None,
                "almanack-score-denominator": None,
                # No metrics, score should be None
                "almanack-score": None,
            },
        ),
    ],
)
def test_compute_almanack_score(
    almanack_table_data: List[Dict[str, Union[int, float, bool]]], expected: float
):
    """
    Tests the compute_almanack_score function.
    """

    result = compute_almanack_score(almanack_table_data)
    assert result == expected, f"Expected {expected}, but got {result}"


@pytest.mark.parametrize(
    "files",
    [
        # basic repo without much
        [
            {"files": {"file2.txt": "Initial content"}},
        ],
        # include a readme
        [
            {"files": {"readme.md": "Initial content"}},
            {"files": {"file2.txt": "More content"}},
        ],
        # Add another valid file to change the table result
        [
            {
                "files": {
                    "readme.md": "Initial content",
                    "citation.cff": "A citation file",
                }
            },
            {"files": {"file2.txt": "More content"}},
        ],
    ],
)
def test_gather_failed_almanack_metric_checks(tmp_path, files):
    """
    Test gather_failed_almanack_metric_checks
    """

    # setup the repo
    repo_setup(repo_path=tmp_path, files=files)

    # calculate the almanack score and the failed metrics
    # independent of one another.
    almanack_score_metrics = compute_almanack_score(
        almanack_table=(get_table(repo_path=tmp_path))
    )
    failed_metrics = gather_failed_almanack_metric_checks(repo_path=tmp_path)

    # calculate the number of expected failures
    # by subtracting the number of successful metrics
    # from the total number of metrics calculated
    # by the almanack score.
    expected_failures = (
        almanack_score_metrics["almanack-score-denominator"]
        - almanack_score_metrics["almanack-score-numerator"]
    )

    # subtract one from the failed_metrics to account for
    # the almanack score within the failed metrics.
    assert expected_failures == len(failed_metrics) - 1

    # check ignores
    failed_metrics_with_ignore = gather_failed_almanack_metric_checks(
        repo_path=tmp_path, ignore=["SGA-GL-0025"]
    )

    assert len(failed_metrics_with_ignore) == len(failed_metrics) - 1


@pytest.mark.parametrize(
    "files, expect_cli, expected_commands",
    [
        (
            {
                "files": {
                    "pyproject.toml": """
[project]
name = "example"
version = "0.1.0"

[project.scripts]
example-cli = "example.module:main"
""",
                }
            },
            True,
            ["example-cli"],
        ),
        (
            {
                "files": {
                    "setup.cfg": """
[options.entry_points]
console_scripts =
    tool-one = pkg.one:main
    tool-two = pkg.two:main
""",
                }
            },
            True,
            ["tool-one", "tool-two"],
        ),
        (
            {
                "files": {
                    "README.md": "# no cli here",
                }
            },
            False,
            None,
        ),
    ],
)
def test_compute_repo_data_cli_detection(
    tmp_path, files, expect_cli, expected_commands
):
    """
    Test CLI entrypoint detection from pyproject.toml and setup.cfg metadata.
    """
    repo_setup(repo_path=tmp_path, files=[files])

    repo_data = compute_repo_data(str(tmp_path))

    assert repo_data["repo-has-cli"] is expect_cli
    if expected_commands is None:
        assert repo_data["repo-cli-entrypoints"] is None
    else:
        assert sorted(repo_data["repo-cli-entrypoints"]) == sorted(expected_commands)


# ---------------------------------------------------------------------------
# Unit tests for extracted helper functions
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "content, expected",
    [
        # Minimal valid conda env with just a name key
        ("name: myenv\n", True),
        # Full conda env with channels and dependencies
        (
            "name: myenv\nchannels:\n  - defaults\ndependencies:\n  - python=3.11\n",
            True,
        ),
        # Only dependencies key
        ("dependencies:\n  - numpy\n", True),
        # Arbitrary YAML with no conda keys
        ("title: My Project\nauthor: someone\n", False),
        # Non-mapping YAML (list at root)
        ("- item1\n- item2\n", False),
        # Invalid YAML
        ("key: [unclosed", False),
        # Empty string
        ("", False),
    ],
)
def test_is_conda_environment_yaml(content, expected):
    """Test is_conda_environment_yaml correctly identifies conda env files."""
    assert is_conda_environment_yaml(content) is expected


@pytest.mark.parametrize(
    "remote_repo_data, expected",
    [
        # Prefer languages_lines key
        (
            {"languages_lines": {"Python": 1000, "Shell": 200}},
            {"Python": 1000, "Shell": 200},
        ),
        # Fall through to languages_loc when languages_lines absent
        ({"languages_loc": {"R": 500}}, {"R": 500}),
        # Fall through to languages key last
        ({"languages": {"Go": 300}}, {"Go": 300}),
        # None values are coerced to 0
        ({"languages": {"Python": None}}, {"Python": 0}),
        # Empty remote data returns empty dict
        ({}, {}),
        # None remote data returns empty dict
        (None, {}),
    ],
)
def test_get_repository_languages_data_from_remote(remote_repo_data, expected):
    """Test _get_repository_languages_data uses remote metadata when available."""
    result = _get_repository_languages_data(
        remote_repo_data=remote_repo_data or {}, remote_url=None
    )
    assert result == expected


@pytest.mark.parametrize(
    "files, remote_repo_data, readme_exists, expected_description",
    [
        # Remote description is preferred
        (
            {"files": {"README.md": "A readme paragraph.\n\nAnother paragraph."}},
            {"description": "Remote description"},
            True,
            "Remote description",
        ),
        # CITATION.cff abstract used when no remote description
        (
            {
                "files": {
                    "CITATION.cff": "abstract: A citation abstract.\n",
                    "README.md": "A readme paragraph.",
                }
            },
            None,
            True,
            "A citation abstract.",
        ),
        # README first non-badge paragraph used as fallback
        (
            {"files": {"README.md": "First paragraph.\n\nSecond paragraph."}},
            None,
            True,
            "First paragraph.",
        ),
        # Badge-only first paragraph is skipped
        (
            {"files": {"README.md": "![badge](url)\n\nReal content."}},
            None,
            True,
            "Real content.",
        ),
        # Nothing available returns None
        (
            {"files": {"setup.py": "pass"}},
            None,
            False,
            None,
        ),
    ],
)
def test_get_software_description(
    tmp_path, files, remote_repo_data, readme_exists, expected_description
):
    """Test _get_software_description priority order across sources."""
    repo = repo_setup(repo_path=tmp_path, files=[files])
    readme_file = find_file(repo=repo, filepath="readme", case_insensitive=True)

    result = _get_software_description(
        repo=repo,
        remote_repo_data=remote_repo_data,
        readme_exists=readme_exists and readme_file is not None,
        readme_file=readme_file,
    )
    assert result == expected_description


@pytest.mark.parametrize(
    "files, expected_commands",
    [
        # poetry scripts
        (
            {
                "files": {
                    "pyproject.toml": (
                        "[tool.poetry]\nname = 'pkg'\n"
                        "[tool.poetry.scripts]\nmycli = 'pkg.mod:main'\n"
                    )
                }
            },
            ["mycli"],
        ),
        # project.scripts (PEP 621)
        (
            {
                "files": {
                    "pyproject.toml": (
                        "[project]\nname = 'pkg'\n"
                        "[project.scripts]\ntool-a = 'pkg.a:run'\ntool-b = 'pkg.b:run'\n"
                    )
                }
            },
            ["tool-a", "tool-b"],
        ),
        # setup.cfg console_scripts
        (
            {
                "files": {
                    "setup.cfg": (
                        "[options.entry_points]\nconsole_scripts =\n"
                        "    cfg-tool = pkg.mod:main\n"
                    )
                }
            },
            ["cfg-tool"],
        ),
        # setup.py entry_points console_scripts
        (
            {
                "files": {
                    "setup.py": (
                        "from setuptools import setup\n"
                        "setup(entry_points={'console_scripts': ['setup-tool = pkg.mod:main']})\n"
                    )
                }
            },
            ["setup-tool"],
        ),
        # No entrypoints found
        (
            {"files": {"README.md": "nothing here"}},
            [],
        ),
    ],
)
def test_get_cli_entrypoints(tmp_path, files, expected_commands):
    """Test _get_cli_entrypoints discovers commands from pyproject.toml and setup.cfg."""
    repo = repo_setup(repo_path=tmp_path, files=[files])
    result = _get_cli_entrypoints(repo=repo)
    assert result == sorted(expected_commands)


@pytest.mark.parametrize(
    "content, expected",
    [
        # Standard setuptools.setup() call
        (
            "from setuptools import setup\n"
            "setup(entry_points={'console_scripts': ['mycli = pkg.mod:main']})\n",
            {"mycli"},
        ),
        # setup() with multiple commands
        (
            "setup(entry_points={'console_scripts': ['a = x:f', 'b = y:g']})\n",
            {"a", "b"},
        ),
        # entry_points present but no console_scripts key
        (
            "setup(entry_points={'gui_scripts': ['app = pkg:main']})\n",
            set(),
        ),
        # No setup() call at all
        (
            "print('hello')\n",
            set(),
        ),
        # Invalid Python syntax returns empty set
        (
            "def (\n",
            set(),
        ),
        # setuptools.setup() attribute-style call
        (
            "import setuptools\n"
            "setuptools.setup(entry_points={'console_scripts': ['attr-cli = pkg:run']})\n",
            {"attr-cli"},
        ),
    ],
)
def test_parse_setup_py_console_scripts(content, expected):
    """Test _parse_setup_py_console_scripts extracts console_scripts via AST."""
    assert _parse_setup_py_console_scripts(content) == expected


def test_get_programming_extensions_returns_frozenset():
    """Test _get_programming_extensions returns a non-empty frozenset of dot-prefixed strings."""
    exts = _get_programming_extensions()
    assert isinstance(exts, frozenset)
    assert len(exts) > 0
    assert all(isinstance(e, str) and e.startswith(".") for e in exts)


def test_get_programming_extensions_cached(monkeypatch):
    """Test _get_programming_extensions returns the same object on repeated calls (cached)."""
    # Reset the cache to force a fresh fetch/fallback cycle.
    monkeypatch.setattr(data_module, "_programming_extensions_cache", None)

    first = _get_programming_extensions()
    second = _get_programming_extensions()
    assert first is second


def test_get_programming_extensions_falls_back_on_network_error(monkeypatch):
    """Test _get_programming_extensions falls back to the static set when fetch fails."""
    monkeypatch.setattr(data_module, "_programming_extensions_cache", None)

    def _raise(*_args, **_kwargs):
        raise requests.ConnectionError("simulated offline")

    monkeypatch.setattr(requests, "get", _raise)

    result = _get_programming_extensions()
    assert result == _FALLBACK_PROGRAMMING_EXTENSIONS


def test_walk_tree_measure_size_of_noncode_files(tmp_path):
    """Test _walk_tree_measure_size_of_noncode_files counts non-code file lines and skips code files."""
    repo = repo_setup(
        repo_path=tmp_path,
        files=[
            {
                "files": {
                    # non-code: 3 lines
                    "docs/notes.txt": "line one\nline two\nline three",
                    # code file — must be skipped
                    "src/main.py": "import os\nprint('hello')\n",
                    # another non-code file
                    "data/info.csv": "a,b\n1,2\n",
                }
            }
        ],
    )

    root_tree = repo.head.peel().tree
    counts = _walk_tree_measure_size_of_noncode_files(root_tree, repo=repo)

    assert ".txt" in counts
    assert ".csv" in counts
    # Python files must not appear in the output
    assert ".py" not in counts


def test_get_repository_languages_data_github_fallback(monkeypatch):
    """Test _get_repository_languages_data falls back to the GitHub API when remote data is empty."""
    monkeypatch.setattr(
        data_module,
        "get_api_data",
        lambda api_endpoint: {"Python": 5000, "Shell": 300},
    )

    result = _get_repository_languages_data(
        remote_repo_data={},
        remote_url="https://github.com/example/repo",
    )
    assert result == {"Python": 5000, "Shell": 300}


def test_get_repository_languages_data_github_fallback_non_github_skipped(monkeypatch):
    """Test _get_repository_languages_data does not call the API for non-GitHub URLs."""
    called = []
    monkeypatch.setattr(data_module, "get_api_data", lambda **_: called.append(1) or {})

    result = _get_repository_languages_data(
        remote_repo_data={},
        remote_url="https://gitlab.com/example/repo",
    )
    assert result == {}
    assert called == []


@pytest.mark.parametrize(
    "content, expected",
    [
        # Poetry convention
        (
            "[tool.poetry.dependencies]\npython = '>=3.10,<3.14'\n",
            ">=3.10,<3.14",
        ),
        # PEP 621
        (
            "[project]\nrequires-python = '>=3.11'\n",
            ">=3.11",
        ),
        # Poetry takes precedence over PEP 621
        (
            "[project]\nrequires-python = '>=3.11'\n[tool.poetry.dependencies]\npython = '>=3.10'\n",
            ">=3.10",
        ),
        # No Python version declared
        (
            "[project]\nname = 'mypkg'\n",
            None,
        ),
        # Invalid TOML returns None
        (
            "key = [unclosed",
            None,
        ),
    ],
)
def test_get_pyproject_python_version(content, expected):
    """Test _get_pyproject_python_version extracts the declared Python version."""
    assert _get_pyproject_python_version(content) == expected


@pytest.mark.parametrize(
    "content, expected",
    [
        # Pinned version with =
        ("name: myenv\ndependencies:\n  - python=3.11\n", "3.11"),
        # Constraint with >=
        ("name: myenv\ndependencies:\n  - python>=3.10\n", "3.10"),
        # No python dep
        ("name: myenv\ndependencies:\n  - numpy\n", None),
        # Empty dependencies
        ("name: myenv\ndependencies: []\n", None),
        # Invalid YAML returns None
        ("key: [unclosed", None),
    ],
)
def test_get_conda_python_version(content, expected):
    """Test _get_conda_python_version extracts the Python version from a conda env YAML."""
    assert _get_conda_python_version(content) == expected


@pytest.mark.parametrize(
    "filename",
    [
        "environment.yml",
        "environment.yaml",
        "conda.yml",
        "conda.yaml",
        "conda-environment.yml",
        "conda-environment.yaml",
    ],
)
def test_conda_detection_alternate_filenames(tmp_path, filename):
    """Test that conda is detected regardless of which conventional filename is used."""
    repo_setup(
        repo_path=tmp_path,
        files=[{"files": {filename: "name: myenv\ndependencies:\n  - python=3.11\n"}}],
    )
    repo_data = compute_repo_data(
        str(tmp_path),
        required_metric_names={
            "repo-environment-managers",
            "repo-declared-python-versions",
        },
    )
    assert "conda" in repo_data["repo-environment-managers"]
    assert "3.11" in repo_data["repo-declared-python-versions"]


def test_get_programming_extensions_parses_linguist(monkeypatch):
    """Test _get_programming_extensions correctly parses a Linguist-shaped YAML response."""
    monkeypatch.setattr(data_module, "_programming_extensions_cache", None)

    minimal_languages_yml = (
        "Python:\n  type: programming\n  extensions:\n    - .py\n    - .pyw\n"
        "Markdown:\n  type: prose\n  extensions:\n    - .md\n"
        "YAML:\n  type: data\n  extensions:\n    - .yml\n    - .yaml\n"
    )

    class _FakeResponse:
        text = minimal_languages_yml

        def raise_for_status(self):
            pass

    monkeypatch.setattr(requests, "get", lambda *_a, **_kw: _FakeResponse())

    exts = _get_programming_extensions()
    assert ".py" in exts
    assert ".pyw" in exts
    # prose/data types must not be included
    assert ".md" not in exts
    assert ".yml" not in exts


@pytest.mark.parametrize(
    "files, expected_dep_managers, expected_has_deps, expected_env_managers, expected_has_env",
    [
        # requirements.txt only → dependency management, no environment management
        (
            {"files": {"requirements.txt": "numpy==1.26\npandas\n"}},
            ["pip"],
            True,
            [],
            False,
        ),
        # setup.py only → dependency management, no environment management
        (
            {
                "files": {
                    "setup.py": (
                        "from setuptools import setup\n"
                        "setup(name='pkg', install_requires=['numpy'])\n"
                    )
                }
            },
            ["pip"],
            True,
            [],
            False,
        ),
        # setup.cfg only → dependency management, no environment management
        (
            {
                "files": {
                    "setup.cfg": (
                        "[metadata]\nname = pkg\n"
                        "[options]\ninstall_requires =\n    numpy\n"
                    )
                }
            },
            ["pip"],
            True,
            [],
            False,
        ),
        # conda env only → environment management, no dependency-only management
        (
            {
                "files": {
                    "environment.yml": (
                        "name: myenv\ndependencies:\n  - python=3.11\n  - numpy\n"
                    )
                }
            },
            [],
            False,
            ["conda"],
            True,
        ),
        # both requirements.txt and conda → both flags True
        (
            {
                "files": {
                    "requirements.txt": "requests\n",
                    "environment.yml": "name: myenv\ndependencies:\n  - python=3.11\n",
                }
            },
            ["pip"],
            True,
            ["conda"],
            True,
        ),
        # nothing → both False
        (
            {"files": {"README.md": "# project\n"}},
            [],
            False,
            [],
            False,
        ),
    ],
)
def test_dependency_vs_environment_managers(  # noqa: PLR0913
    tmp_path,
    files,
    expected_dep_managers,
    expected_has_deps,
    expected_env_managers,
    expected_has_env,
):
    """Test that dependency management and environment management are correctly separated."""
    repo_setup(repo_path=tmp_path, files=[files])
    repo_data = compute_repo_data(
        str(tmp_path),
        required_metric_names={
            "repo-dependency-managers",
            "repo-has-declared-dependencies",
            "repo-environment-managers",
            "repo-has-managed-environment",
        },
    )

    assert (repo_data["repo-dependency-managers"] or []) == expected_dep_managers
    assert repo_data["repo-has-declared-dependencies"] is expected_has_deps
    assert (repo_data["repo-environment-managers"] or []) == expected_env_managers
    assert repo_data["repo-has-managed-environment"] is expected_has_env
