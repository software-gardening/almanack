"""
Testing repository clean-up
"""

import pathlib

# Constants
TEST_DIRECTORY = pathlib.Path(__file__).resolve().parent
ENTROPY_PATH = TEST_DIRECTORY / "data" / "almanack" / "entropy"


def test_entropy_repos_deleted():
    """
    Test if the high_entropy and low_entropy repositories are deleted.
    """
    high_entropy_path = ENTROPY_PATH / "high_entropy"
    low_entropy_path = ENTROPY_PATH / "low_entropy"

    # Check if the directories are deleted
    assert not high_entropy_path.exists(), f"{high_entropy_path} still exists"
    assert not low_entropy_path.exists(), f"{low_entropy_path} still exists"
