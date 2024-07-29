"""
Sets up Git repositories with baseline content, adds entropy, and commits changes.
"""

import pathlib

import git

from .insert_code import add_LOC


def commit_changes(repo_path: pathlib.Path, message: str) -> None:
    """
    Commits changes in the given repository path with the provided commit message.

    Args:
        repo_path (pathlib.Path): The path to the Git repository.
        message (str): The commit message.
    """
    repo = git.Repo(repo_path)
    repo.git.add(A=True)
    repo.index.commit(message)


def create_repositories(base_path: pathlib.Path) -> None:
    """
    Sets up Git repositories with baseline content and adds entropy.

    Args:
        base_path (pathlib.Path): The base path where repositories will be created.

    Notes:
        Repository Structure:

            Test_repo_1:
                - File_1.md (Lines Changed: 61)
                - File_2.md (Lines Changed: 31)
                - File_3.md (Lines Changed: 16)
            Test_repo_2:
                - File_1.md (Lines Changed: 16)

        The baseline content is committed first, followed by additional lines of changes.
        Each repository will have exactly two commits: one for the baseline content and
        one for the added lines of code.
    """
    # Create directories for test_repo_1 and test_repo_2
    for repo_name in ["3_file_repo", "1_file_repo"]:
        repo_path = base_path / repo_name
        repo_path.mkdir(parents=True, exist_ok=True)
        repo = git.Repo.init(repo_path)

        if repo_name == "3_file_repo":
            for i in range(1, 4):  # Create three files for test_repo_1
                md_file = repo_path / f"file_{i}.md"
                # Add baseline content to Markdown files
                with open(md_file, "w") as f:
                    f.write("Baseline content")
                repo.index.add([str(md_file)])
            repo.index.commit("Committed baseline content to test_repo_1")

        elif repo_name == "1_file_repo":
            md_file = repo_path / "file_1.md"
            # Add baseline content to the Markdown file
            with open(md_file, "w") as f:
                f.write("Baseline content")
            repo.index.add([str(md_file)])
            repo.index.commit("Committed baseline content to test_repo_2")

    # Run the add_entropy.py module to insert additional lines
    add_LOC(base_path)

    # Commit changes after adding entropy
    for repo_name in ["3_file_repo", "1_file_repo"]:
        repo_path = base_path / repo_name
        commit_changes(repo_path, "Commit with added lines of code")
