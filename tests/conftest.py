"""
conftest.py for pytest fixtures and other related aspects.
see: https://docs.pytest.org/en/7.1.x/reference/fixtures.html
"""

import pathlib
import subprocess

import pytest


@pytest.fixture()
def jupyter_book_source():
    """
    Fixture for Jupyter Book content.
    """

    # return the location of the almanac content
    return "src/almanac"


@pytest.fixture()
def build_jupyter_book(jupyter_book_source: str, tmp_path: pathlib.Path):
    """
    Fixture to build Jupyter Book content.

    Note: we use the command line interface for Jupyter Book as this is
    well documented and may have alignment with development tasks.
    """
    print(type(tmp_path))

    # build jupyter book content
    result = subprocess.run(
        ["jupyter-book", "build", jupyter_book_source, "--path-output", tmp_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # check that the build returns 0 (nothing failed)
    assert result.returncode == 0

    return tmp_path
