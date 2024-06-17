"""
This script initializes a Git repository, adds baseline content to Markdown files,
and introduces entropy through the 'add_entropy.py' script

Functions:
- `commit changes`: Takes in a Git repository, and adds/commits to the given repo.

References:
- The 'add_entropy.py' script defines the specific content changes for entropy introduction.

Command-Line Instructions:
- To invoke this script within the development environment, use the following command:
  poetry run python add_data.py

"""

import pathlib
import subprocess

from add_entropy import add_entropy


def commit_changes(directory: dir, message: str):
    """
    Commits changes in the specified Git directory with a given commit message.

    Args:
        directory (dir): The directory containing the Git repository.
        message (str): The commit message.
    """
    subprocess.run(["git", "add", "."], check=True, cwd=directory)
    subprocess.run(["git", "commit", "-m", message], check=True, cwd=directory)


def main():
    # Create directories for high_entropy and low_entropy
    for dir_name in ["high_entropy", "low_entropy"]:
        pathlib.Path(dir_name).mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init"], check=True, cwd=dir_name)

    # Add baseline content to Markdown files and commit
    baseline_text = """
    Baseline content
    """
    md_files = ["high_entropy/high_entropy.md", "low_entropy/low_entropy.md"]
    for md_file in md_files:
        with open(md_file, "w") as f:
            f.write(baseline_text)
        directory = pathlib.Path(md_file).parent
        commit_changes(directory, "Initial commit with baseline content")

    # Run the add_entropy.py script
    add_entropy()

    # Commit changes after adding entropy
    for dir_name in ["high_entropy", "low_entropy"]:
        commit_changes(dir_name, "Commit with added entropy")


if __name__ == "__main__":
    main()
