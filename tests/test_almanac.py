"""
Testing Python package for almanac.
"""

import pytest

from almanac import read


def test_read(capsys) -> None:
    """
    Test reading of content from the book through a package.

    Note: we use capsys here from pytest to help capture stdout.
    See here for more:
    https://docs.pytest.org/en/7.1.x/how-to/capture-stdout-stderr.html
    """

    # test that we raise a lookup error with no input
    with pytest.raises(LookupError):
        read()

    # read a file for comparison below
    with open("src/book/garden-circle/contributing.md", mode="r") as file:
        control = file.read()

    # read example content
    read(chapter_name="contributing")

    # capture the output
    test_capture = capsys.readouterr()

    # Check if the printed output contains the expected content
    # note: we split out the newlines for equal comparisons.
    assert control == "\n".join(line.strip() for line in test_capture.out.splitlines())
