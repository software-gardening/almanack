"""
Tests CLI functionality.
"""
import json

from .utils import run_cli_command
from tests.data.almanack.repo_setup.create_repo import repo_setup

def test_cli_util():
    """
    Test the run_cli_command for successful output
    """

    command = """echo 'hello world'"""
    _, _, returncode = run_cli_command(command)

    assert returncode == 0

def test_cli_almanack(tmp_path):
    """
    Tests running `almanack` as a CLI
    """

    repo = repo_setup(
        repo_path=tmp_path, files={"example.txt": "example"}, branch_name="master"
    )

    stdout, stderr, returncode = run_cli_command(f"almanack {tmp_path}")

    print(stdout)

    assert returncode == 0

    assert isinstance((result := json.loads(f"[{stdout}]")), dict)
