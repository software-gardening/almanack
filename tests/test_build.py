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

    # run linkchecker against build
    result = subprocess.run(
        [
            "linkchecker",
            f"{build_jupyter_book}/",
            "--ignore-url",
            f"html/_static",
            # used to check external-facing links
            "--check-extern",
            # used to avoid warnings triggering a non-zero return
            "--no-warnings",
            # used to specify a config
            "--config=./.linkcheckerrc.ini",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    check_subproc_run_for_nonzero(completed_proc=result)


def test_web_accessibility(build_jupyter_book: pathlib.Path) -> None:
    """
    Test web accessibility for the Jupyter Book build (html pages) using
    pa11y npm package.

    Note: we use the command line interface for pa11y to leverage
    cross-language capability through python (pa11y is a node.js package)
    """

    # gather all html pages from the build
    for html_page in pathlib.Path(f"{build_jupyter_book}/_build/html").glob("*.html"):
        # check each subproc result
        check_subproc_run_for_nonzero(
            completed_proc=subprocess.run(
                [
                    "npx",
                    "pa11y",
                    html_page,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        )
