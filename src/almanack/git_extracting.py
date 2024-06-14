import git

def get_commit_logs(repository_path):
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
        if commit.hexsha not in logs:
            logs[commit.hexsha] = {
                "message": commit.message,
                "timestamp": commit.authored_date,
                "files": get_commit_contents(repository_path, commit.hexsha),
            }
    return logs


def get_commit_contents(repository_path, commit_id):
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


def main():
    repositories = {
        "high_entropy": "/home/willdavidson/Desktop/Almanack/almanac/tests/data/almanack/entropy/high_entropy",
        "low_entropy": "/home/willdavidson/Desktop/Almanack/almanac/tests/data/almanack/entropy/low_entropy",
    }

    all_logs = {}
    for repo_name, repo_path in repositories.items():
        all_logs[repo_name] = get_commit_logs(repo_path)
    return all_logs

if __name__ == "__main__":
    logs = main()
