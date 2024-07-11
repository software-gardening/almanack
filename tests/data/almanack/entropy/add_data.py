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
    """

    # Create directories for high_entropy and low_entropy
    for dir_name in ["test_repo_1", "test_repo_2"]:
        repo_path = base_path / dir_name
        pathlib.Path(repo_path).mkdir(parents=True, exist_ok=True)
        git.Repo.init(repo_path)

        if dir_name == "test_repo_1":
            for i in range(1, 4):  # Create three files for test_repo_1
                md_file = repo_path / f"file_{i}.md"
                # Add baseline content to Markdown files
                baseline_text = "Baseline content"
                with open(md_file, "w") as f:
                    f.write(baseline_text)
        elif dir_name == "test_repo_2":
            md_file = repo_path / f"file_1.md"
            # Add baseline content to the Markdown file
            baseline_text = "Baseline content"
            with open(md_file, "w") as f:
                f.write(baseline_text)

        # Commit baseline content
        commit_changes(repo_path, "Initial commit with baseline content")

    # Run the add_entropy.py module
    insert_entropy(base_path)

    # Commit changes after adding entropy
    for dir_name in ["test_repo_1", "test_repo_2"]:
        repo_path = base_path / dir_name
        commit_changes(repo_path, "Commit with added entropy")
