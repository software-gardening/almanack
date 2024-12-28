"""
This module focuses on the Almanack's Garden Lattice materials
which encompass aspects of human understanding.
"""

import logging
import pathlib

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import defusedxml.ElementTree as ET
import pygit2
import requests
import yaml

from ...git import (
    clone_repository,
    count_files,
    find_file,
    get_commits,
    get_edited_files,
    get_remote_url,
    read_file,
    file_exists_in_repo
)
from ..entropy.calculate_entropy import (
    calculate_aggregate_entropy,
    calculate_normalized_entropy,
)


METRICS_TABLE = f"{pathlib.Path(__file__).parent!s}/metrics.yml"
DATETIME_NOW = datetime.now(timezone.utc)

LOGGER = logging.getLogger(__name__)

def is_citable(repo: pygit2.Repository) -> bool:
    """
    Check if the given repository is citable.

    A repository is considered citable if it contains a CITATION.cff or CITATION.bib
    file, or if the README.md file contains a citation section indicated by "## Citation"
    or "## Citing".

    Args:
        repo (pygit2.Repository): The repository to check for citation files.

    Returns:
        bool: True if the repository is citable, False otherwise.
    """

    # Check for a CITATION.cff or CITATION.bib file
    if file_exists_in_repo(
        repo=repo,
        expected_file_name="citation",
        check_extension=True,
        extensions=[".cff", ".bib"],
    ):
        return True

    # Look for a README.md file and read its content
    if (
        file_content := read_file(
            repo=repo, filepath="readme.md", case_insensitive=True
        )
    ) is not None:
        # Check for an H2 heading indicating a citation section
        if any(
            check_string in file_content
            for check_string in [
                # markdown sub-headers
                "## Citation",
                "## Citing",
                "## Cite",
                "## How to cite",
                # RST sub-headers
                "Citation\n--------",
                "Citing\n------",
                "Cite\n----",
                "How to cite\n-----------",
                # DOI shield
                "[![DOI](https://img.shields.io/badge/DOI",
            ]
        ):
            return True

    return False

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
