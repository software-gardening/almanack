"""
This module performs git operations
"""

import pathlib
import tempfile
from typing import Dict, List, Optional

import pygit2
from charset_normalizer import from_bytes


def clone_repository(repo_url: str) -> pathlib.Path:
    """
    Clones the GitHub repository to a temporary directory.

    Args:
        repo_url (str): The URL of the GitHub repository.

    Returns:
        pathlib.Path: Path to the cloned repository.
    """
    # Create a temporary directory to store the cloned repository
    temp_dir = tempfile.mkdtemp()
    # Define the path for the cloned repository within the temporary directory
    repo_path = pathlib.Path(temp_dir) / "repo"
    # Clone the repository from the given URL into the defined path
    pygit2.clone_repository(repo_url, str(repo_path))
    return repo_path


def get_commits(repo: pygit2.Repository) -> List[pygit2.Commit]:
    """
    Retrieves the list of commits from the main branch.

    Args:
        repo (pygit2.Repository): The Git repository.

    Returns:
        List[pygit2.Commit]: List of commits in the repository.
    """
    # Get the latest commit (HEAD) from the repository
    head = repo.revparse_single("HEAD")
    # Create a walker to iterate over commits starting from the HEAD
    walker = repo.walk(
        head.id, pygit2.enums.SortMode.NONE
    )  #  SortMode.NONE traverses commits in natural order; no sorting applied.
    # Collect all commits from the walker into a list
    commits = list(walker)
    return commits


def get_edited_files(
    repo: pygit2.Repository,
    source_commit: pygit2.Commit,
    target_commit: pygit2.Commit,
) -> List[str]:
    """
    Finds all files that have been edited, added, or deleted between two specific commits.

    Args:
        repo (pygit2.Repository): The Git repository.
        source_commit (pygit2.Commit): The source commit.
        target_commit (pygit2.Commit): The target commit.

    Returns:
        List[str]: List of file names that have been edited, added, or deleted between the two commits.
    """

    # Create a set to store unique file names that have been edited
    file_names = set()
    # Get the differences (diff) between the source and target commits
    diff = repo.diff(source_commit, target_commit)
    # Iterate through each patch in the diff
    for patch in diff:
        # If the old file path is present, add it to the set
        if patch.delta.old_file.path:
            file_names.add(patch.delta.old_file.path)
        # If the new file path is present, add it to the set
        if patch.delta.new_file.path:
            file_names.add(patch.delta.new_file.path)
    return list(file_names)


def get_loc_changed(
    repo_path: pathlib.Path, source: str, target: str, file_names: List[str]
) -> Dict[str, int]:
    """
    Finds the total number of code lines changed for each specified file between two commits.

    Args:
        repo_path (pathlib.Path): The path to the git repository.
        source (str): The source commit hash.
        target (str): The target commit hash.
        file_names (List[str]): List of file names to calculate changes for.

    Returns:
        Dict[str, int]: A dictionary where the key is the filename, and the value is the lines changed (added and removed).
    """
    repo = pygit2.Repository(str(repo_path))

    # Resolve the source and target commits by their hashes
    source_commit = repo.revparse_single(source)
    target_commit = repo.revparse_single(target)

    changes = {}
    # Compute the diff between the source and target commits
    diff = repo.diff(source_commit, target_commit)

    # Iterate over each patch in the diff
    for patch in diff:
        if patch.delta.new_file.path in file_names:
            additions = 0
            deletions = 0
            # Iterate over each hunk in the patch
            for hunk in patch.hunks:
                # Iterate over each line in the hunk
                for line in hunk.lines:
                    if line.origin == "+":
                        additions += 1
                    elif line.origin == "-":
                        deletions += 1
            lines_changed = additions + deletions
            # Store the number of lines changed for the file
            changes[patch.delta.new_file.path] = lines_changed

    return changes


def get_most_recent_commits(repo_path: pathlib.Path) -> tuple[str, str]:
    """
    Retrieves the two most recent commit hashes in the test repositories

    Args:
        repo_path (pathlib.Path): The path to the git repository.

    Returns:
        tuple[str, str]: Tuple containing the source and target commit hashes.
    """
    repo = pygit2.Repository(str(repo_path))
    commits = get_commits(repo)

    # Assumes that commits are sorted by time, with the most recent first
    source_commit = commits[1]  # Second most recent
    target_commit = commits[0]  # Most recent

    return str(source_commit.id), str(target_commit.id)


"""
Module for handling various tasks with git repo blobs.
"""


import pygit2


def detect_encoding(blob_data: bytes) -> str:
    """
    Detect the encoding of the given blob data using charset-normalizer.

    Args:
        blob_data (bytes): The raw bytes of the blob to analyze.

    Returns:
        str: The best detected encoding of the blob data.

    Raises:
        ValueError: If no encoding could be detected.
    """
    if not blob_data:
        raise ValueError("No data provided for encoding detection.")

    result = from_bytes(blob_data)
    if result.best():
        # Get the best encoding found
        return result.best().encoding
    raise ValueError("Encoding could not be detected.")


def find_file(
    repo: pygit2.Repository, filepath: str, case_insensitive: bool = False
) -> Optional[pygit2.Object]:
    """
    Locate a file in the repository by its path.

    Args:
        repo (pygit2.Repository):
            The repository object.
        filepath (str):
            The path to the file within the repository.
        case_insensitive (bool):
            If True, perform case-insensitive comparison.

    Returns:
        Optional[pygit2.Object]:
            The entry of the found file,
            or None if no matching file is found.
    """
    tree = repo.head.peel().tree
    found_entry = None

    if not case_insensitive:
        try:
            found_entry = tree[filepath]
        except KeyError:
            return None
    else:
        path_parts = filepath.lower().split("/")
        for i, part in enumerate(path_parts):
            try:
                entry = next(e for e in tree if e.name.lower() == part)
            except StopIteration:
                return None

            if entry.type == pygit2.GIT_OBJECT_TREE:
                tree = repo[entry.id]
            elif entry.type == pygit2.GIT_OBJECT_BLOB:
                if i == len(path_parts) - 1:
                    found_entry = entry
                    break
                else:
                    return None
            else:
                return None

    return found_entry


def read_file(
    repo: pygit2.Repository,
    entry: Optional[pygit2.Object] = None,
    filepath: Optional[str] = None,
    case_insensitive: bool = False,
) -> Optional[str]:
    """
    Read the content of a file from the repository.

    Args:
        repo (pygit2.Repository):
            The repository object.
        entry (Optional[pygit2.Object]):
            The entry of the file to read. If not provided, filepath must be specified.
        filepath (Optional[str]):
            The path to the file within the repository. Used if entry is not provided.
        case_insensitive (bool):
            If True, perform case-insensitive comparison when using filepath.

    Returns:
        Optional[str]:
            The content of the file as a string,
            or None if the file is not found or reading fails.
    """
    if entry is None:
        if filepath is None:
            raise ValueError("Either entry or filepath must be provided.")
        entry = find_file(repo, filepath, case_insensitive)
        if entry is None:
            return None

    try:
        blob = repo[entry.id]
        blob_data: bytes = blob.data
        decoded_data = blob_data.decode(detect_encoding(blob_data))
        return decoded_data
    except (AttributeError, UnicodeDecodeError):
        return None
