"""
This module procesess GitHub data 
"""

import json
import pathlib

from almanack.reporting.report import whole_repo_report
from almanack.processing.generate_data import generate_whole_repo_data


def process_repo_entropy(repo_path: str) -> None:
    """
    CLI entry point to process a repository for calculating entropy changes between commits and
    generate a report.

    Args:
        repo_path (str): The local path to the Git repository.
    """

    repo_path = pathlib.Path(repo_path)

    # Check if the directory contains a Git repository
    if not repo_path.exists() or not (repo_path / ".git").exists():
        raise FileNotFoundError(f"The directory {repo_path} is not a repository")

    # Process the repository and get the dictionary
    entropy_data = generate_whole_repo_data(str(repo_path))

    # Generate and print the report from the dictionary
    report_content = whole_repo_report(entropy_data)

    # Convert the dictionary to a JSON string
    json_string = json.dumps(entropy_data, indent=4)

    print(report_content)

    # Return the JSON string and report content
    return json_string