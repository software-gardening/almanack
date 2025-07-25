"""
Test git operations functionality
"""

import pathlib
from datetime import datetime
from typing import Any, Dict, List
from urllib.parse import urlparse

import pygit2
import pytest

from almanack.git import (
    clone_repository,
    count_files,
    detect_encoding,
    file_exists_in_repo,
    find_file,
    get_commits,
    get_edited_files,
    get_loc_changed,
    get_most_recent_commits,
    get_remote_url,
    read_file,
)
from tests.data.almanack.repo_setup.create_repo import repo_setup


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

        # Check that repo_path in the output is the same as the input
        # (so long as we know the path is consistent and not "temp",
        # as it would be for an http link to a repo).
        if str(repo_path).startswith("http"):
            repo_path = clone_repository(repo_url=str(repo_path))  # noqa: PLW2901

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


@pytest.mark.parametrize(
    "files, expected_count",
    [
        # Test case: Single file at root
        ([{"files": {"file1.txt": "content"}}], 1),
        # Test case: Multiple files at root
        ([{"files": {"file1.txt": "content", "file2.txt": "content"}}], 2),
        # Test case: Files in nested directories
        (
            [
                {
                    "files": {
                        "dir1/file1.txt": "content",
                        "dir1/dir2/file2.txt": "content",
                    }
                }
            ],
            2,
        ),
        # Test case: Empty repository (no files)
        ([{"files": {}}], 0),
        # Test case: Mixed root and nested files
        (
            [
                {
                    "files": {
                        "file1.txt": "content",
                        "dir1/file2.txt": "content",
                        "dir1/dir2/file3.txt": "content",
                    }
                }
            ],
            3,
        ),
    ],
)
def test_count_files(
    files: List[Dict[str, str]], expected_count: int, tmp_path: pathlib.Path
):
    """
    Test the count_files function on various repository structures.

    Args:
        files (List[Dict[str, str]]): A list of dictionaries where each dictionary represents a commit
            and contains filenames as keys and file content as values.
        expected_count (int): The expected number of files in the most recent commit tree.
        tmp_path (pathlib.Path): Temporary directory path provided by pytest for testing.
    """
    # Set up the test repository
    repo_path = tmp_path / "test_repo"
    repo = repo_setup(repo_path, files=files)

    # Get the most recent commit and its tree
    most_recent_commit = next(repo.walk(repo.head.target, pygit2.GIT_SORT_TIME))
    most_recent_tree = most_recent_commit.tree

    # Run the count_files function and assert the file count matches the expected count
    assert (
        count_files(most_recent_tree) == expected_count
    ), f"Expected {expected_count} files, got {count_files(most_recent_tree)}"


def test_get_remote_url(tmp_path: pathlib.Path, current_repo: str):
    """
    Test get_remote_url using the repository containing this test.
    """

    # Call the function to get the remote URL
    remote_url = get_remote_url(current_repo)

    # Assert that a remote URL is found
    assert remote_url is not None, "No remote URL found for the current repository."

    # Validate the remote URL structure
    parsed_url = urlparse(remote_url)
    assert parsed_url.scheme in {
        "http",
        "https",
        "ssh",
    }, f"Unexpected scheme in URL: {parsed_url.scheme}"
    assert parsed_url.netloc, f"Invalid net location in URL: {remote_url}"

    # Optionally, print the remote URL for debugging
    print(f"Remote URL: {remote_url}")

    # create a repo and check that the origin is captured (instead of upstream)
    pathlib.Path(repo_path := (tmp_path / "test_remote_repo")).mkdir(
        parents=True, exist_ok=True
    )
    origin_repo = pygit2.init_repository(str(repo_path), bare=False)
    origin_url = "https://github.com/org/repo.git"
    origin_repo.remotes.create("origin", origin_url)

    remote_url = get_remote_url(origin_repo)

    # we check that we have the modified url without the git suffix
    assert remote_url == origin_url.replace(
        ".git", ""
    ), f"Expected remote URL {origin_url}, but got {remote_url}"


@pytest.mark.parametrize(
    "expected_file_name, check_extension, extensions, expected_result",
    [
        ("readme", True, [".md", ""], True),
        ("README", False, [], True),
        ("CONTRIBUTING", True, [".md", ""], True),
        ("contributing", False, [], True),
        ("code_of_conduct", True, [".md", ""], True),
        ("CODE_OF_CONDUCT", False, [], True),
        ("LICENSE", True, [".md", ".txt", ""], True),
        ("license", False, [], True),
    ],
)
def test_file_exists_in_repo(
    community_health_repository_path: pygit2.Repository,
    expected_file_name: str,
    check_extension: bool,
    extensions: List[str],
    expected_result: bool,
):
    """
    Combined test for file_exists_in_repo function using different scenarios.
    """

    result = file_exists_in_repo(
        repo=community_health_repository_path,
        expected_file_name=expected_file_name,
        check_extension=check_extension,
        extensions=extensions,
    )

    assert result == expected_result

    # test the almanack itself
    repo_path = pathlib.Path(".").resolve()
    repo = pygit2.Repository(str(repo_path))

    result = file_exists_in_repo(
        repo=repo,
        expected_file_name=expected_file_name,
        check_extension=check_extension,
        extensions=extensions,
    )

    assert result == expected_result


@pytest.mark.parametrize(
    # test various scenarios of repositories
    # and the expected filename returned
    # when using the find_file function.
    "repo_files, filepath, case_insensitive, extensions, expected_filename",
    [
        (
            [
                {
                    "files": {
                        "README.md": "# Sample Repo",
                        "CONTRIBUTING.md": "Contribution guidelines",
                    },
                    "commit-date": datetime(2023, 1, 1),
                    "author": {"name": "Author One", "email": "author1@example.com"},
                },
            ],
            "README",
            False,
            [".md", ".txt", ".rtf", ".rst", ""],
            "README.md",
        ),
        (
            [
                {
                    "files": {
                        "readme.md": "# Sample Repo",
                    },
                    "commit-date": datetime(2023, 1, 1),
                    "author": {"name": "Author One", "email": "author1@example.com"},
                },
            ],
            "README",
            True,
            [".md", ".txt", ".rtf", ".rst", ""],
            "readme.md",
        ),
        (
            [
                {
                    "files": {
                        "docs/index.rst": "Documentation index",
                    },
                    "commit-date": datetime(2023, 1, 1),
                    "author": {"name": "Author One", "email": "author1@example.com"},
                },
            ],
            "docs/index",
            False,
            [".md", ".txt", ".rtf", ".rst", ""],
            "index.rst",
        ),
        (
            [
                {
                    "files": {
                        "README.txt": "Sample Repo in text format",
                    },
                    "commit-date": datetime(2023, 1, 1),
                    "author": {"name": "Author One", "email": "author1@example.com"},
                },
            ],
            "README",
            False,
            [".md", ".txt", ".rtf", ".rst", ""],
            "README.txt",
        ),
    ],
)
def test_find_file(  # noqa: PLR0913
    repo_files: List[Dict[str, Dict[str, str]]],
    filepath: str,
    case_insensitive: bool,
    extensions: List[str],
    expected_filename: str,
    tmp_path: pathlib.Path,
) -> None:
    """
    Tests the almanack.git.find_file function with various types of repositories.
    """

    # Set up the repository with the provided files
    repo_path = tmp_path / "test_repo"
    repo = repo_setup(repo_path, repo_files)

    # Find the file in the repo
    file_entry = find_file(repo, filepath, case_insensitive, extensions)

    # Check that the file entry is found and matches the expected filename
    assert file_entry is not None, f"File {filepath} not found in the repository."
    assert (
        file_entry.name == expected_filename
    ), f"Expected {expected_filename}, but found {file_entry.name}."
