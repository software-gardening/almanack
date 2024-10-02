"""
Testing utilities
"""

import subprocess


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
