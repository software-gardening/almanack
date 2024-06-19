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

def setup_repositories():
    """
    Sets up Git repositories with baseline content and adds entropy.
    """
    # Compute the base path relative to the location of this script
    base_path = pathlib.Path(__file__).resolve().parent

    # Create directories for high_entropy and low_entropy
    for dir_name in ["high_entropy", "low_entropy"]:
        repo_path = base_path / dir_name
        pathlib.Path(repo_path).mkdir(parents=True, exist_ok=True)
        git.Repo.init(repo_path)

        # Add baseline content to Markdown files and commit
        baseline_text = """
        Baseline content
        """
        md_file = repo_path / f"{dir_name}.md"
        with open(md_file, "w") as f:
            f.write(baseline_text)
        commit_changes(repo_path, "Initial commit with baseline content")

    # Commit changes after creating baseline content
    for dir_name in ["high_entropy", "low_entropy"]:
        repo_path = base_path / dir_name
        commit_changes(repo_path, "Commit with baseline content")

    # Run the add_entropy.py script
    add_entropy()

    # Commit changes after adding entropy
    for dir_name in ["high_entropy", "low_entropy"]:
        repo_path = base_path / dir_name
        commit_changes(repo_path, "Commit with added entropy")

setup_repositories

