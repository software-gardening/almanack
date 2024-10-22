"""
Module for handling various tasks with git repo blobs.
"""

from typing import Optional

import pygit2
from charset_normalizer import from_bytes


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


def find_and_read_file(repo: pygit2.Repository, filename: str) -> Optional[str]:
    """
    Find and read the content of a file in the repository that matches the filename pattern.

    Args:
        repo (str): The path to the repository.
        filename (str): The pattern to match against filenames.

    Returns:
        Optional[str]: The content of the found file, or None if no matching files are found.
    """

    # Get the tree associated with the latest commit
    tree = repo.head.peel().tree

    # find the first occurrence of a matching file
    found_file: Optional[pygit2.Blob] = next(
        (
            entry
            for entry in tree
            if entry.type == pygit2.GIT_OBJECT_BLOB
            and filename.lower() == entry.name.lower()
        ),
        None,
    )

    # if we have none, return it early to avoid trying to read nothing
    if found_file is None:
        return found_file

    # Read the content of the first found blob
    blob_data: bytes = found_file.data

    # Decode and return content as a string
    return blob_data.decode(detect_encoding(blob_data))
