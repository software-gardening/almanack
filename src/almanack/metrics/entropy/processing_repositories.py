"""
This module procesess GitHub data
"""

import pathlib

from almanack.metrics.data import compute_pr_data, compute_repo_data
from almanack.reporting.report import pr_report, repo_report


def process_repo_entropy(repo_path: str) -> str:
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

    print(report_content)  # noqa: T201


def process_pr_entropy(repo_path: str, pr_branch: str, main_branch: str) -> str:
    """
    Processes GitHub PR data to calculate a report comparing the PR branch to the main branch.

    Args:
        repo_path (str): The local path to the Git repository.
        pr_branch (str): The branch name of the PR.
        main_branch (str): The branch name for the main branch.

    Returns:
        str: A JSON string containing report data.

    Raises:
        FileNotFoundError: If the specified directory does not contain a valid Git repository.
    """

    repo_path = pathlib.Path(repo_path)

    # Check if the directory contains a Git repository
    if not repo_path.exists() or not (repo_path / ".git").exists():
        raise FileNotFoundError(f"The directory {repo_path} is not a repository")

    # Process the PR and get the dictionary
    pr_data = compute_pr_data(str(repo_path), pr_branch, main_branch)

    # Generate and print the report
    report_content = pr_report(pr_data)

    print(report_content)  # noqa: T201
