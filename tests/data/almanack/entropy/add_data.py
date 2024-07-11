"""
Sets up Git repositories with baseline content, adds entropy, and commits changes.
"""

import pathlib

import git

from .add_entropy import insert_entropy


def commit_changes(directory: str, message: str) -> None:
    """
    Commits changes in the specified Git directory with a given commit message.

    Args:
        directory (str): The directory containing the Git repository.
        message (str): The commit message.
    """
    repo = git.Repo(directory)
    repo.git.add(".")
    repo.index.commit(message)


def create_repositories(base_path: pathlib.Path) -> None:
    """
    Sets up Git repositories with baseline content and adds entropy.
    Repositories Structure:
        High_Entropy
            - high_entropy.md
                - Baseline Content
                - Added Entropy
            - high_entropy2.md
                -Baseline content
        Low_Entropy
            -Low_entropy.md
                - Baseline content
                - Added entropy
    """
    # Create and initialize directories for high_entropy and low_entropy
    for dir_name in ["high_entropy", "low_entropy"]:
        repo_path = base_path / dir_name
        repo_path.mkdir(parents=True, exist_ok=True)
        git.Repo.init(repo_path)

        # Create a markdown file with baseline content
        with open(repo_path / f"{dir_name}.md", "w") as f:
            f.write("Baseline content")

            # Add a second file in the high_entropy repository and commit baseline content
        with open(base_path / "high_entropy/high_entropy2.md", "w") as f:
            f.write("Baseline content")

        # Commit the initial baseline content
        commit_changes(repo_path, "Initial commit with baseline content")

    # Run the add_entropy.py module
    insert_entropy(base_path)

    # Commit changes after adding entropy
    for dir_name in ["high_entropy", "low_entropy"]:
        with open(base_path / "high_entropy/high_entropy2.md", "w") as f:
            f.write("List of Number: 1\n,2\n,3\n,4\n,5\n,6\n,7\n8\n,9\n")
        commit_changes(base_path / dir_name, "Commit with added entropy")
