"""
This module creates entropy reports
"""

import json
import pathlib
from typing import Dict, Any 
import tabulate

from almanack.processing.processing_repositories import process_entire_repo


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
    entropy_data = process_entire_repo(str(repo_path))

    # Generate and print the report from the dictionary
    report_content = whole_repo_report(entropy_data)

    # Convert the dictionary to a JSON string
    json_string = json.dumps(entropy_data, indent=4)

    print(report_content)

    # Return the JSON string and report content
    return json_string


def whole_repo_report(data: Dict[str, Any]) -> str:
    """
    Returns the formatted entropy report as a string.

    Args:
        data (Dict[str, Any]): Dictionary with the entropy data.

    Returns:
        str: Formatted entropy report.
    """
    title = "Entropy Analysis Report"

    # Extract details from data
    repo_path = data["repo_path"]
    total_normalized_entropy = data["total_normalized_entropy"]
    number_of_commits = data["number_of_commits"]
    number_of_files = data["number_of_files"]
    time_range_of_commits = data["time_range_of_commits"]
    entropy_data = data[
        "file_level_entropy"
    ]  # Assume this contains entropy for each file

    # Sort files by normalized entropy in descending order and get the top 5
    sorted_entropy = sorted(
        entropy_data.items(), key=operator.itemgetter(1), reverse=True
    )
    top_files = sorted_entropy[:5]

    # Format the report
    repo_info = [
        ["Repository Path", repo_path],
        ["Total Normalized Entropy", f"{total_normalized_entropy:.4f}"],
        ["Number of Commits Analyzed", number_of_commits],
        ["Files Analyzed", number_of_files],
        [
            "Time Range of Commits",
            f"{time_range_of_commits[0]} to {time_range_of_commits[1]}",
        ],
    ]

    top_files_info = [
        [file_name, f"{normalized_entropy:.4f}"]
        for file_name, normalized_entropy in top_files
    ]

    report_content = f"""
{'=' * 80}
{title:^80}
{'=' * 80}

Repository Information:
{tabulate(repo_info, tablefmt="simple_grid")}

Top 5 Files with the Most Entropy:
{tabulate(top_files_info, headers=["File Name", "Normalized Entropy"], tablefmt="simple_grid")}

"""
    return report_content
