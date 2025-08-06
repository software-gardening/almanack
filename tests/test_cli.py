"""
Tests CLI functionality.
"""

import json

import yaml

from almanack.cli import cli_link
from almanack.metrics.data import METRICS_TABLE
from tests.data.almanack.repo_setup.create_repo import repo_setup

from .utils import run_cli_command


def test_cli_link():
    """
    Test the cli_link function to ensure
    it generates the correct link format.
    """

    link = cli_link(
        uri="https://example.com",
        label="Example Link",
    )

    assert isinstance(link, str)
    assert "Example Link" in link
    assert "https://example.com" in link

    link = cli_link(
        uri="https://example.com",
    )

    assert isinstance(link, str)
    assert "https://example.com" in link
    assert link.count("https://example.com") == 2  # noqa: PLR2004


def test_cli_util():
    """
    Test the run_cli_command for successful output
    """

    _, _, returncode = run_cli_command(["echo", "'hello world'"])

    assert returncode == 0


def test_cli_almanack_table(tmp_path):
    """
    Tests running `almanack table` as a CLI
    """

    # create a repo with a single file and commit
    repo = repo_setup(repo_path=tmp_path, files=[{"files": {"example.txt": "example"}}])

    # gather output and return code from running a CLI command
    stdout, _, returncode = run_cli_command(command=["almanack", "table", repo.path])

    # make sure we return 0 on success
    assert returncode == 0

    # gather result of CLI as json
    results = json.loads(stdout)

    # make sure we have a list of output
    assert isinstance(results, list)

    # open the metrics table
    with open(METRICS_TABLE, "r") as f:
        metrics_table = yaml.safe_load(f)

    # check that all keys exist in the output from metrics table to cli str
    assert all(
        x == y
        for x, y in zip(
            sorted([result["name"] for result in results]),
            sorted([metric["name"] for metric in metrics_table["metrics"]]),
        )
    )

    # gather output and return code from running a CLI command
    # and ignore one metric
    stdout, _, returncode = run_cli_command(
        command=["almanack", "table", repo.path, "--ignore", "'SGA-GL-0002'"]
    )
    assert "SGA-GL-0002" not in stdout

    # gather file-based data
    stdout, _, returncode = run_cli_command(
        command=["almanack", "table", repo.path, str(tmp_path / "example.json")]
    )

    with open(str(tmp_path / "example.json"), "r") as f:
        results2 = json.load(f)

    # remove datetime focused results
    results2 = [val for val in results2 if val["name"] != "almanack-table-datetime"]
    results = [val for val in results if val["name"] != "almanack-table-datetime"]

    assert results == results2


def test_cli_almanack_check(tmp_path):
    """
    Tests running `almanack check` as a CLI
    """

    almanack_failed_check_exit_code = 2

    # create a repo with a single file and commit
    repo = repo_setup(repo_path=tmp_path, files=[{"files": {"example.txt": "example"}}])

    # gather output and return code from running a CLI command
    stdout, _, returncode = run_cli_command(command=["almanack", "check", repo.path])

    # make sure we return 1 on failures
    # (the example repo likely has many failures)
    assert returncode == almanack_failed_check_exit_code

    # check that we see the following strings within the output
    assert all(
        check_str in stdout
        # We check for generalized strings within the output below.
        # Note: actual text may vary - the text here is mostly about
        # ensuring the output was roughly provided without
        # so much precision that we have to adjust these strings
        # with each minor change.
        for check_str in [
            "Running Software Gardening Almanack checks.",
            "Datetime:",
            "Almanack version:",
            "Target repository path:",
            "The following Software Gardening Almanack metrics",
            "Software Gardening Almanack summary:",
        ]
    )

    # gather output and return code from running a CLI command
    stdout, _, returncode = run_cli_command(
        command=[
            "almanack",
            "check",
            repo.path,
            "--ignore",
            "'SGA-GL-0002','SGA-GL-0026'",
        ]
    )

    # make sure we return 1 on failures
    # (the example repo likely has many failures)
    assert returncode == almanack_failed_check_exit_code

    # check that we don't see the following id's within the output
    # (we ignored them)
    assert all(item not in stdout for item in ["SGA-GL-0002", "SGA-GL-0026"])

    # check that the CLI functions when the terminal
    # colwidth is very small.
    stdout, _, returncode = run_cli_command(
        command=["env", "COLUMNS=1", "almanack", "check", repo.path]
    )

    # we assert that the return code is still 2
    # (return code of 1 would mean exception)
    assert returncode == almanack_failed_check_exit_code
