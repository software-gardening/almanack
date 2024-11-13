"""
Tests CLI functionality.
"""

import json

import yaml

from almanack.metrics.data import METRICS_TABLE
from tests.data.almanack.repo_setup.create_repo import repo_setup

from .utils import run_cli_command


def test_cli_util():
    """
    Test the run_cli_command for successful output
    """

    _, _, returncode = run_cli_command(["echo", "'hello world'"])

    assert returncode == 0


def test_cli_almanack(tmp_path):
    """
    Tests running `almanack` as a CLI
    """

    # create a repo with a single file and commit
    repo = repo_setup(repo_path=tmp_path, files={"example.txt": "example"})

    # gather output and return code from running a CLI command
    stdout, _, returncode = run_cli_command(command=["almanack", repo.path])

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
