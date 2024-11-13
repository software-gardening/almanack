"""
Functions for creating test repositories in order to
test almanack capabilities.
"""

import pathlib

import pygit2

from .insert_code import add_LOC


def set_repo_user_config(repo):
    """
    Sets user.name and user.email in the repository config.

    Args:
        repo (pygit2.Repository): The repository object.
    """
    config = repo.config
    config["user.name"] = "A Name"  # Replace with your name
    config["user.email"] = "an_email@example.com"  # Replace with your email


def commit_changes(repo_path: pathlib.Path, message: str) -> None:
    """
    Commits changes in the given repository path with the provided commit message.

    Args:
        repo_path (pathlib.Path): The path to the Git repository.
        message (str): The commit message.
    """

    # Open the repository
    repo = pygit2.Repository(str(repo_path))

    # Stage all changes (equivalent to `git add .`)
    index = repo.index
    index.add_all()
    index.write()

    # Get author and committer information
    signature = repo.default_signature

    # Commit the changes
    tree = index.write_tree()
    parent_commit = repo.head.target
    repo.create_commit(
        "refs/heads/main",  # reference where to commit
        signature,  # author
        signature,  # committer
        message,  # commit message
        tree,  # tree object for the commit
        [parent_commit],  # parent commit (list for merge commits)
    )

    # set the head to the main branch
    repo.set_head("refs/heads/main")


def create_entropy_repositories(base_path: pathlib.Path) -> None:
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
        repo = pygit2.init_repository(path=str(repo_path), bare=False)

        # Set user.name and user.email in the config
        set_repo_user_config(repo)

        if repo_name == "3_file_repo":
            for i in range(1, 4):  # Create three files for test_repo_1
                md_file = repo_path / f"file_{i}.md"
                # Resolve the file path to avoid path issues
                md_file = md_file.resolve()

                # Add baseline content to Markdown files
                with open(md_file, "w") as f:
                    f.write("Baseline content")

                # Add the file to the index
                repo.index.add(
                    str(md_file.relative_to(repo_path))
                )  # Relative path is crucial
            repo.index.write()
            tree = repo.index.write_tree()
            author = repo.default_signature
            repo.create_commit(
                "refs/heads/main",  # reference
                author,  # author
                author,  # committer
                "Committed baseline content to test_repo_1",  # message
                tree,  # tree object
                [],  # no parents for initial commit
            )

            # set the head to the main branch
            repo.set_head("refs/heads/main")

        elif repo_name == "1_file_repo":
            md_file = repo_path / "file_1.md"
            # Resolve the file path to avoid path issues
            md_file = md_file.resolve()

            # Add baseline content to the Markdown file
            with open(md_file, "w") as f:
                f.write("Baseline content")

            # Add the file to the index
            repo.index.add(
                str(md_file.relative_to(repo_path))
            )  # Relative path is crucial
            repo.index.write()
            tree = repo.index.write_tree()
            author = repo.default_signature
            repo.create_commit(
                "refs/heads/main",  # reference
                author,  # author
                author,  # committer
                "Committed baseline content to test_repo_2",  # message
                tree,  # tree object
                [],  # no parents for initial commit
            )

            # set the head to the main branch
            repo.set_head("refs/heads/main")

    # Run the add_entropy.py module to insert additional lines
    add_LOC(base_path)

    # Commit changes after adding entropy
    for repo_name in ["3_file_repo", "1_file_repo"]:
        repo_path = base_path / repo_name
        commit_changes(repo_path, "Commit with added lines of code")


def repo_setup(
    repo_path: pathlib.Path, files: dict, branch_name: str = "main"
) -> pygit2.Repository:
    """
    Set up a temporary repository with specified files.
    Args:
        repo_path (Path):
            The directory where the repo will be created.
        files (dict):
            A dictionary where keys are filenames and values are their content.
        branch_name (str):
            A string with the name of the branch which will be used for
            committing changes. Defaults to "main".
    Returns:
        pygit2.Repository: The initialized repository with files.
    """
    # Create a new repository in the specified path
    repo = pygit2.init_repository(repo_path, bare=False)

    # Set user.name and user.email in the config
    set_repo_user_config(repo)

    # Create nested files in the repository
    for file_path, content in files.items():
        full_path = repo_path / file_path  # Construct full path
        full_path.parent.mkdir(
            parents=True, exist_ok=True
        )  # Create any parent directories
        full_path.write_text(content)  # Write the file content

    # Stage and commit the files
    index = repo.index
    index.add_all()
    index.write()

    author = repo.default_signature
    tree = repo.index.write_tree()

    # Commit the files
    repo.create_commit(
        f"refs/heads/{branch_name}",
        author,
        author,
        "Initial commit with setup files",
        tree,
        [],
    )

    # Set the HEAD to point to the new branch
    repo.set_head(f"refs/heads/{branch_name}")

    return repo
