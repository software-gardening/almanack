"""
Functions for creating test repositories in order to
test almanack capabilities.
"""

import pathlib
from datetime import datetime

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
    repo_path: pathlib.Path,
    files: list[dict],
    branch_name: str = "main",
) -> pygit2.Repository:
    """
    Set up a temporary repository with specified files and commit metadata.

    Args:
        repo_path (pathlib.Path):
            The temporary directory where the repo will be created.
        files (list[dict]):
            A list of dictionaries where each dictionary represents a commit.
            Each dictionary must have:
                - "files": A dictionary of filenames as keys and file content as values.
                - "commit-date" (optional): The datetime of the commit.
                - "author" (optional): A dictionary with "name" and "email" keys
                  to specify the commit author. If not provided, defaults to the
                  repository's default user configuration.
                - "tag" (optional): A string representing the tag to associate
                  with the commit.

        branch_name (str):
            The name of the branch to use for commits. Defaults to "main".

    Returns:
        pygit2.Repository:
            The initialized repository with the specified commits and tags.
    """
    # Initialize the repository
    repo = pygit2.init_repository(repo_path, bare=False)

    # Set user.name and user.email in the config
    set_repo_user_config(repo)

    branch_ref = f"refs/heads/{branch_name}"
    parent_commit = None

    # Loop through each commit dictionary in `files`
    for i, commit_data in enumerate(files):
        # Extract commit files and metadata
        commit_files = commit_data.get("files", {})
        commit_date = commit_data.get("commit-date", datetime.now())
        author_data = commit_data.get("author", None)
        tag_name = commit_data.get("tag")  # Get the optional tag name

        # Create or update each file in the current commit
        for filename, content in commit_files.items():
            file_path = repo_path / filename
            file_path.parent.mkdir(
                parents=True, exist_ok=True
            )  # Ensure parent directories exist
            file_path.write_text(content)

        # Stage all changes in the index
        index = repo.index
        index.add_all()
        index.write()

        # Determine the author and committer
        if author_data:
            author = pygit2.Signature(
                author_data["name"],
                author_data["email"],
                int(commit_date.timestamp()),
            )
        else:
            author = pygit2.Signature(
                repo.default_signature.name,
                repo.default_signature.email,
                int(commit_date.timestamp()),
            )
        committer = author  # Assuming the committer is the same as the author

        # Write the index to a tree
        tree = index.write_tree()

        # Create the commit
        commit_message = f"Commit #{i + 1} with files: {', '.join(commit_files.keys())}"
        commit_id = repo.create_commit(
            (
                branch_ref if i == 0 else None
            ),  # Set branch reference only for the first commit
            author,
            committer,
            commit_message,
            tree,
            (
                [parent_commit.id] if parent_commit else []
            ),  # Use the .id attribute to get the commit ID
        )

        # Update the parent_commit to the latest commit for chaining
        parent_commit = repo.get(commit_id)

        # Create a tag if specified
        if tag_name:
            repo.create_tag(
                tag_name,
                parent_commit.id,
                pygit2.GIT_OBJECT_COMMIT,
                author,
                f"Tag {tag_name} for commit #{i + 1}",
            )

    # Set the HEAD to the main branch after all commits
    repo.set_head(branch_ref)

    # Ensure the HEAD is pointing to the last commit
    repo.head.set_target(parent_commit.id)

    return repo
