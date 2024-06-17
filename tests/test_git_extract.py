import pathlib

# Constants
ENTROPY_PATH = "/home/willdavidson/Desktop/Almanack/almanac/tests/data/almanack/entropy"


def test_entropy_repos_deleted():
    """
    Test if the high_entropy and low_entropy repositories are deleted.
    """
    # Check if the directories are deleted
    assert not (pathlib.Path(ENTROPY_PATH) / "high_entropy").exists()
    assert not (pathlib.Path(ENTROPY_PATH) / "low_entropy").exists()
