import os
from pathlib import Path
import pytest
from src.almanack.git_extracting import get_commit_logs, get_commit_contents  # Replace with your actual module name

def find_git_repo(starting_path):
    """Searches for a .git folder starting from the given path and going up the directory tree."""
    path = Path(starting_path).resolve()
    for parent in [path] + list(path.parents):
        if (parent / '.git').is_dir():
            return parent
    raise FileNotFoundError("No .git directory found")

# Use the current directory as the starting point
try:
    REPO_PATH = find_git_repo(Path.cwd())
except FileNotFoundError as e:
    REPO_PATH = None
    print(e)

@pytest.mark.skipif(REPO_PATH is None, reason="No .git repository found in the current or parent directories.")
def test_get_commit_logs():
    logs = get_commit_logs(REPO_PATH)
    assert isinstance(logs, dict), "get_commit_logs should return a dictionary"
    assert len(logs) > 0, "get_commit_logs should return at least one commit"
    sample_commit = next(iter(logs.values()))
    assert 'message' in sample_commit, "Each commit should have a 'message' key"
    assert 'timestamp' in sample_commit, "Each commit should have a 'timestamp' key"
    assert 'files' in sample_commit, "Each commit should have a 'files' key"

@pytest.mark.skipif(REPO_PATH is None, reason="No .git repository found in the current or parent directories.")
def test_get_commit_contents():
    logs = get_commit_logs(REPO_PATH)
    sample_commit_id = next(iter(logs.keys()))
    contents = get_commit_contents(REPO_PATH, sample_commit_id)
    assert isinstance(contents, dict), "get_commit_contents should return a dictionary"
    # If there are files in the commit, check that their content is a string
    if contents:
        sample_file_content = next(iter(contents.values()))
        assert isinstance(sample_file_content, str), "File content should be a string"

if __name__ == "__main__":
    pytest.main()
