# import os
# from pathlib import Path
# import pytest
# from src.almanack.git_extracting import get_commit_logs, get_commit_contents  # Replace with your actual module name

# def find_git_repo(starting_path):
#     """Searches for a .git folder starting from the given path and going up the directory tree."""
#     path = Path(starting_path).resolve()
#     for parent in [path] + list(path.parents):
#         if (parent / '.git').is_dir():
#             return parent
#     raise FileNotFoundError("No .git directory found")

# # Use the current directory as the starting point
# try:
#     REPO_PATH = find_git_repo(Path.cwd())
# except FileNotFoundError as e:
#     REPO_PATH = None
#     print(e)
