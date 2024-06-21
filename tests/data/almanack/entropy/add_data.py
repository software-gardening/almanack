"""
Sets up Git repositories with baseline content, adds entropy, and commits changes.
"""

import pathlib

import git

from .add_entropy import add_entropy


def commit_changes(directory: str, message: str):
    """
    Commits changes in the specified Git directory with a given commit message.

    Args:
        directory (str): The directory containing the Git repository.
        message (str): The commit message.
    """
    repo = git.Repo(directory)
    repo.git.add(".")
    repo.index.commit(message)


def create_repositories(base_path: str):
    """
    Sets up Git repositories with baseline content and adds entropy.
    """

    # Create directories for high_entropy and low_entropy
    for dir_name in ["high_entropy", "low_entropy"]:
        repo_path = base_path / dir_name
        pathlib.Path(repo_path).mkdir(parents=True, exist_ok=True)
        git.Repo.init(repo_path)

        md_file = repo_path / f"{dir_name}.md"
        # Add baseline content to Markdown files
        baseline_text = """
            Baseline content
            """
        with open(md_file, "w") as f:
            f.write(baseline_text)

        # Commit baseline content
        commit_changes(repo_path, "Initial commit with baseline content")

    # Run the add_entropy.py scriptwhat
    add_entropy(base_path)

    # Commit changes after adding entropy
    for dir_name in ["high_entropy", "low_entropy"]:
        repo_path = base_path / dir_name
        commit_changes(repo_path, "Commit with added entropy")
