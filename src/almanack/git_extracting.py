"""
This module retrieves Git logs and commit contents for specified repositories.
"""

from pathlib import Path

import git


def get_commit_logs(repository_path: str):
    """
    Retrieves Git logs for a given repository.

    Args:
        repository_path (str): The path to the Git repository.

    Returns:
        dict: A dictionary mapping repository names to dictionaries of commit IDs and their details.
              Example: {'repository_name': {'commit_id': {'message': 'Commit message', 'timestamp': 1234567890}}}
    """
    logs = {}
    repo = git.Repo(repository_path)
    for commit in repo.iter_commits():
        logs[commit.hexsha] = {
            "message": commit.message,
            "timestamp": commit.authored_date,
            "files": get_commit_contents(repository_path, commit.hexsha),
        }
    return logs


def get_commit_contents(repository_path: str, commit_id: str):
    """
    Retrieves contents of a specific commit in a Git repository.

    Args:
        repository_path (str): The path to the Git repository.
        commit_id (str): The commit ID to retrieve contents from.

    Returns:
        dict: A dictionary mapping file names to their contents.
              Example: {'filename': 'file_content'}
    """
    contents = {}
    repo = git.Repo(repository_path)
    commit = repo.commit(commit_id)

    for file_path in commit.tree.traverse():
        contents[file_path.path] = file_path.data_stream.read().decode("utf-8")

    return contents


def main(repositories):
    all_logs = {}
    for repo_name, repo_path in repositories.items():
        # Retrieve commit logs for each repository and store them in the dictionary
        all_logs[repo_name] = get_commit_logs(repo_path)
    print(f"All logs: {all_logs}")
    return all_logs

