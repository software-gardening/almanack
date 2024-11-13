"""
Test git operations functionality
"""

import pathlib
from typing import Any

import pygit2
import pytest

from almanack.git import (
    clone_repository,
    detect_encoding,
    find_file,
    get_commits,
    get_edited_files,
    get_loc_changed,
    get_most_recent_commits,
    read_file,
)


def test_clone_repository(entropy_repository_paths: dict[str, Any]):
    repo_path = entropy_repository_paths["3_file_repo"]

    # Call the function
    cloned_path = clone_repository(str(repo_path))

    # Assert that the cloned repository path exists
    assert cloned_path.exists()


def test_get_commits(entropy_repository_paths: dict[str, Any]):
    # Open the repo
    repo_path = entropy_repository_paths["3_file_repo"]
    repo = pygit2.Repository(str(repo_path))

    # Call the function
    commits = get_commits(repo)

    # Assert that commits are in a list
    assert isinstance(commits, list)
    # Assert that there is at least one commit
    assert len(commits) > 0


def test_get_edited_files(entropy_repository_paths: dict[str, Any]):
    # Open the repo
    repo_path = entropy_repository_paths["3_file_repo"]
    repo = pygit2.Repository(str(repo_path))

    # Get commits to use for comparison
    commits = get_commits(repo)
    source_commit = commits[-1]  # Use the earliest commit as source
    target_commit = commits[0]  # Use the latest commit as target

    # Call the function
    edited_files = get_edited_files(repo, source_commit, target_commit)

    # Assert that the edited files list is not negative
    assert len(edited_files) >= 0


def test_get_loc_changed(
    entropy_repository_paths: dict[str, pathlib.Path],
    repo_file_sets: dict[str, list[str]],
) -> None:
    """
    Test the calculate_loc_changes function.
    """

    results = {}

    for label, repo_path in entropy_repository_paths.items():
        # Extract two most recent commits: source and target
        source_commit, target_commit = get_most_recent_commits(repo_path)
        # Call loc_changes function on test repositories
        loc_changes = get_loc_changed(
            repo_path, source_commit, target_commit, repo_file_sets[label]
        )
        results[label] = loc_changes
    assert all(
        file_name in loc_changes for file_name in repo_file_sets[label]
    )  # Check that file_sets[label] are present keys
    assert all(
        change >= 0 for change in loc_changes.values()
    )  # Check that all values are non-negative


def test_get_most_recent_commits(entropy_repository_paths: dict[str, Any]):
    repo_path = entropy_repository_paths["3_file_repo"]

    # Call the function to get the two most recent commits
    source_commit_hash, target_commit_hash = get_most_recent_commits(repo_path)

    # Open the repository and retrieve all commits
    repo = pygit2.Repository(str(repo_path))
    commits = get_commits(repo)
    MIN_COMMITS = 2
    # Ensure there are at least two commits
    assert len(commits) >= MIN_COMMITS

    # Validate the commit hashes match
    assert source_commit_hash == str(commits[1].id)
    assert target_commit_hash == str(commits[0].id)


@pytest.mark.parametrize(
    "byte_data, expected_encoding, should_raise",
    [
        (
            b"\xef\xbb\xbf\xf0\x9f\xa9\xb3",
            "utf_8",
            False,
        ),  # Test detection of UTF-8 encoding
        (b"", None, True),  # Test detection on empty byte sequence
        # Add more test cases here if needed
    ],
)
def test_detect_encoding(byte_data, expected_encoding, should_raise):
    """Test detection of encoding based on various byte inputs."""
    if should_raise:
        with pytest.raises(ValueError):
            detect_encoding(byte_data)
    else:
        detected_encoding = detect_encoding(byte_data)
        assert detected_encoding == expected_encoding


@pytest.mark.parametrize(
    "filename, expected_content",
    [
        ("README.md", "## Citation"),
        ("readme", None),
        ("nonexistent.txt", None),
    ],
)
def test_find_file_and_read_file(
    repo_with_citation_in_readme, filename, expected_content
):
    """
    Test finding and reading files in the repository with various filename patterns.
    """

    find_file_result = find_file(repo=repo_with_citation_in_readme, filepath=filename)
    # test for none returns
    if expected_content is None:
        assert find_file_result is expected_content
        assert (
            read_file(repo=repo_with_citation_in_readme, filepath=filename)
            is expected_content
        )

    # test for content
    else:
        assert isinstance(find_file_result, pygit2.Object)
        read_file_result_filepath = read_file(
            repo=repo_with_citation_in_readme, filepath=filename
        )
        read_file_result_pygit_obj = read_file(
            repo=repo_with_citation_in_readme, entry=find_file_result
        )

        assert read_file_result_filepath == expected_content
        assert read_file_result_filepath == read_file_result_pygit_obj
