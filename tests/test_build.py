"""
Testing content builds and related aspects.
"""

import pathlib
import subprocess

from conftest import check_subproc_run_for_nonzero


def test_links(build_jupyter_book: pathlib.Path) -> None:
    """
    Test links for the Jupyter Book build (html pages) using
    linkchecker python package.

    Note: we use the command line interface for linkchecker as this is
    well documented and may have alignment with development tasks.
    """

    # build jupyter book content
    result = subprocess.run(
        [
            "linkchecker",
            f"{build_jupyter_book}/",
            # we ignore _static files which include special templating features
            # which would otherwise cause errors during link checks
            "--ignore-url",
            f"html/_static",
            # used to check external-facing links
            "--check-extern",
            # used to avoid warnings triggering a non-zero return
            "--no-warnings",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    check_subproc_run_for_nonzero(completed_proc=result)
