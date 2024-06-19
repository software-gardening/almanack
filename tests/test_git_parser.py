# test_name.py

import pytest
import pathlib
import shutil
from data.almanack.entropy.add_data import setup_repositories
from almanack.git_parser import collect_all_commit_logs  # Adjust import path as per your structure

@pytest.fixture(scope="session")
def repository_paths():
    """
    Fixture to provide the paths to the test repositories.
    """
    # Compute the base path relative to the location of this conftest script
    base_path = pathlib.Path(__file__).resolve().parent / "../tests/data/almanack/entropy"

    # Run add_data.py to set up the repositories
    setup_repositories()

    repositories = {
        "high_entropy": base_path / "high_entropy",
        "low_entropy": base_path / "low_entropy",
    }

    yield repositories
    # Delete the high_entropy and low_entropy directories to sustain repository structure
    shutil.rmtree(base_path / "high_entropy", ignore_errors=True)
    shutil.rmtree(base_path / "low_entropy", ignore_errors=True)
def test_main(repository_paths: dict[str, pathlib.Path]):
    all_logs = collect_all_commit_logs(repository_paths)

    # Check that the logs contain entries for both repositories
    assert "high_entropy" in all_logs
    assert "low_entropy" in all_logs

