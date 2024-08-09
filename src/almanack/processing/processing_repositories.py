"""
This module procesess GitHub data
"""

import json
import pathlib

from almanack.processing.compute_data import compute_repo_data
from almanack.reporting.report import repo_report


def process_repo_entropy(repo_path: str) -> None:
    """
    Processes GitHub repository data to calculate a report.

    Args:
        repo_path (str): The local path to the Git repository.

    Returns:
        str: A JSON string containing the repository data and entropy metrics.

    Raises:
        FileNotFoundError: If the specified directory does not contain a valid Git repository.
    """

    repo_path = pathlib.Path(repo_path)

    # Check if the directory contains a Git repository
    if not repo_path.exists() or not (repo_path / ".git").exists():
        raise FileNotFoundError(f"The directory {repo_path} is not a repository")

    # Process the repository and get the dictionary
    entropy_data = compute_repo_data(str(repo_path))

    # Generate and print the report from the dictionary
    report_content = repo_report(entropy_data)

    # Convert the dictionary to a JSON string
    json_string = json.dumps(entropy_data)

    print(report_content)

    # Return the JSON string and report content
    return json_string
