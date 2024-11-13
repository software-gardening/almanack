"""
Testing utilities
"""

import subprocess
from typing import Tuple


def check_subproc_run_for_nonzero(completed_proc: subprocess.CompletedProcess) -> None:
    """
    Checks subprocess.CompletedProcess for errors and displays stdout
    in a legible way through pytest.
    """

    try:
        # check that the build returns 0 (nothing failed)
        assert completed_proc.returncode == 0
    except Exception as exc:
        # raise the exception with decoded output from linkchecker for readability
        raise Exception(completed_proc.stdout.decode()) from exc


def run_cli_command(command: str) -> Tuple[str, str, int]:
    """
    Run a CLI command using subprocess and capture the output and return code.

    Args:
        command (list): The command to run as a list of strings.

    Returns:
        tuple: (str: stdout, str: stderr, int: returncode)
    """

    result = subprocess.run(args=command, capture_output=True, text=True, check=False)
    return result.stdout, result.stderr, result.returncode
