"""
This script initializes a Git repository, adds baseline content to Markdown files,
introduces entropy through the 'add_entropy.py' script, and zips the resulting
files .git directories.

Functions:
- `zip_git_folder(folder_path, output_zip_path)`: Takes in a folder path, performs a zip on that folder, and outputs a zip file.

References:
- The 'add_entropy.py' script defines the specific content changes for entropy introduction.

Command-Line Instructions:
- To invoke this script within the development environment, use the following command:
  poetry run python add_data.py

- To unzip the created zip files and view the contents, use the following commands:
  unzip high_entropy_git.zip -d high_entropy_unzipped
  unzip low_entropy_git.zip -d low_entropy_unzipped
"""

import pathlib
import subprocess
import zipfile
from pathlib import Path

from add_entropy import add_entropy


def zip_git_folder(folder_path: str, output_zip_path: str):
    """
    Creates a zip file containing the contents of a folder.

    Args:
        folder_path (str): The path to the folder to be zipped.
        output_zip_path (str): The path to the output zip file.
    """
    folder_path = Path(folder_path)
    output_zip_path = Path(output_zip_path)

    with zipfile.ZipFile(output_zip_path, "w") as zipf:
        for file_path in folder_path.glob("**/*"):
            if file_path.is_file():
                zipf.write(file_path, file_path.relative_to(folder_path))


def commit_changes(directory: str, message: str):
    """
    Commits changes in the specified Git directory with a given commit message.

    Args:
        directory (str): The directory containing the Git repository.
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
        directory = Path(md_file).parent
        commit_changes(directory, "Initial commit with baseline content")

    # Run the add_entropy.py script
    add_entropy()

    # Commit changes after adding entropy
    for dir_name in ["high_entropy", "low_entropy"]:
        commit_changes(dir_name, "Commit with added entropy")

    # Ensure that .git folders are present and zip them
    for dir_name in ["high_entropy", "low_entropy"]:
        zip_git_folder(f"{dir_name}/.git", f"{dir_name}_git.zip")


if __name__ == "__main__":
    main()