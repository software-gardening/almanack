"""
Testing content builds and related aspects.
"""

import pathlib
import subprocess


def test_links(build_jupyter_book: pathlib.Path):
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
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        # check that the build returns 0 (nothing failed)
        assert result.returncode == 0
    except Exception as exc:
        # raise the exception with decoded output from linkchecker for readability
        raise Exception(result.stdout.decode()) from exc
