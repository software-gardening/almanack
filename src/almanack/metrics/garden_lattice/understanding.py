"""
This module focuses on the Almanack's Garden Lattice materials
which encompass aspects of human understanding.
"""

import logging
import pathlib
from datetime import datetime, timezone

import pygit2

from almanack.git import find_file

METRICS_TABLE = f"{pathlib.Path(__file__).parent!s}/metrics.yml"
DATETIME_NOW = datetime.now(timezone.utc)

LOGGER = logging.getLogger(__name__)


def includes_common_docs(repo: pygit2.Repository) -> bool:
    """
    Check whether the repo includes common documentation files and directories
    associated with building docsites.

    Args:
        repo (pygit2.Repository):
            The repository object.

    Returns:
        bool:
            True if any common documentation files
            are found, False otherwise.
    """
    # List of common documentation file paths to check for
    common_docs_paths = [
        "docs/mkdocs.yml",
        "docs/conf.py",
        "docs/index.md",
        "docs/index.rst",
        "docs/index.html",
        "docs/readme.md",
        "docs/source/readme.md",
        "docs/source/index.rst",
        "docs/source/index.md",
        "docs/src/readme.md",
        "docs/src/index.rst",
        "docs/src/index.md",
    ]

    # Check each documentation path using the find_file function
    for doc_path in common_docs_paths:
        if find_file(repo=repo, filepath=doc_path) is not None:
            return True  # Return True as soon as we find any of the files

    # otherwise return false as we didn't find documentation
    return False
