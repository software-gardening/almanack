"""
This module performs git operations
"""

import pathlib
import tempfile
from typing import Dict, List, Optional, Union
from urllib.parse import urlparse

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
    # sorting by time.
    walker = repo.walk(head.id, pygit2.GIT_SORT_TIME)
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
    repo: pygit2.Repository,
    filepath: str,
    case_insensitive: bool = False,
    extensions: list[str] = [".md", ".txt", ".rtf", ".rst", ""],
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
        extensions (list[str]):
            List of possible file extensions to check (e.g., [".md", ""]).

    Returns:
        Optional[pygit2.Object]:
            The entry of the found file,
            or None if no matching file is found.
    """
    # Get the tree object of the latest commit
    tree = repo.head.peel().tree

    # Iterate over each extension to check for the file
    for ext in extensions:
        full_path = f"{filepath}{ext}"  # Construct the full path with the extension
        if not case_insensitive:
            try:
                # Try to get the file entry directly (case-sensitive)
                return tree[full_path]
            except KeyError:
                continue  # If not found, continue to the next extension
        else:
            # Split the path into parts for case-insensitive comparison
            path_parts = full_path.lower().split("/")
            current_tree = tree
            for i, part in enumerate(path_parts):
                try:
                    # Find the entry in the current tree that matches the part (case-insensitive)
                    entry = next(e for e in current_tree if e.name.lower() == part)
                except StopIteration:
                    break  # If no matching entry is found, break the loop

                if entry.type == pygit2.GIT_OBJECT_TREE:
                    # If the entry is a tree, update the current tree to this entry
                    current_tree = repo[entry.id]
                elif entry.type == pygit2.GIT_OBJECT_BLOB:
                    # If the entry is a blob and it's the last part, return the entry
                    if i == len(path_parts) - 1:
                        return entry
                    else:
                        break  # If it's not the last part, break the loop
                else:
                    break  # If the entry is neither a tree nor a blob, break the loop

    # Return None if no valid file is found
    return None


def count_files(tree: Union[pygit2.Tree, pygit2.Blob]) -> int:
    """
    Counts all files (Blobs) within a Git tree, including files
    in subdirectories.

    This function recursively traverses the provided `tree`
    object to count each file, represented as a `pygit2.Blob`,
    within the tree and any nested subdirectories.

    Args:
        tree (Union[pygit2.Tree, pygit2.Blob]):
            The Git tree object (of type `pygit2.Tree`)
            to traverse and count files. The initial call
            should be made with the root tree of a commit.

    Returns:
        int:
            The total count of files (Blobs) within the tree,
            including nested files in subdirectories.
    """
    if isinstance(tree, pygit2.Blob):
        # Directly return 1 if the input is a Blob
        return 1
    elif isinstance(tree, pygit2.Tree):
        # Recursively count files for Tree
        return sum(count_files(entry) for entry in tree)
    else:
        # If neither, return 0
        return 0


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


def get_remote_url(repo: pygit2.Repository) -> Optional[str]:
    """
    Determines the remote URL of a git repository, if available.
    We use the `upstream` remote first, then `origin`,
    and finally any other remote.
    The upstream remote is preferred because it will be used
    for referential data lookups (such as GitHub issues, stars, etc.).

    Args:
        repo (pygit2.Repository): The pygit2 repository object.

    Returns:
        Optional[str]: The remote URL if found, otherwise None.
    """
    # use upstream and then origin to try and find the correct remote URL
    for name in ("upstream", "origin"):
        try:
            # Get the 'origin' remote URL (common convention)
            remote = repo.remotes[name]
            remote_url = remote.url.removesuffix(".git")

            # Validate the URL structure using urlparse
            parsed_url = urlparse(remote_url)
            if parsed_url.scheme in {"http", "https", "ssh"} and parsed_url.netloc:
                return remote_url
        except (KeyError, AttributeError):
            # 'origin' remote does not exist or URL is not accessible
            pass

    # Fallback: Try to get any remote URL if 'origin' does not exist
    try:
        for remote in repo.remotes:
            remote_url = remote.url
            parsed_url = urlparse(remote_url)
            if parsed_url.scheme in {"http", "https", "ssh"} and parsed_url.netloc:
                return remote_url.removesuffix(".git")
    except AttributeError:
        pass

    # Return None if no valid URL is found
    return None


def file_exists_in_repo(
    repo: pygit2.Repository,
    expected_file_name: str,
    check_extension: bool = False,
    extensions: list[str] = [".md", ".txt", ".rtf", ""],
) -> bool:
    """
    Check if a file (case-insensitive and with optional extensions)
    exists in the latest commit of the repository.

    Args:
        repo (pygit2.Repository):
            The repository object to search in.
        expected_file_name (str):
            The base file name to check (e.g., "readme").
        check_extension (bool):
            Whether to check the extension of the file or not.
        extensions (list[str]):
            List of possible file extensions to check (e.g., [".md", ""]).

    Returns:
        bool:
            True if the file exists, False otherwise.
    """

    # Gather a tree from the HEAD of the repo
    tree = repo.revparse_single("HEAD").tree

    # Normalize expected file name to lowercase for case-insensitive comparison
    expected_file_name = expected_file_name.lower()

    for entry in tree:
        # Normalize entry name to lowercase
        entry_name = entry.name.lower()

        # Check if the base file name matches with any allowed extension
        if check_extension and any(
            entry_name == f"{expected_file_name}{ext.lower()}" for ext in extensions
        ):
            return True

        # Check whether the filename without an extension matches the expected file name
        if not check_extension and entry_name.split(".", 1)[0] == expected_file_name:
            return True

    return False
