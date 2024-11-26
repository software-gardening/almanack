"""
conftest.py for pytest fixtures and other related aspects.
see: https://docs.pytest.org/en/7.1.x/reference/fixtures.html
"""

import pathlib
import shutil
import subprocess

import pygit2
import pytest

from tests.data.almanack.repo_setup.create_repo import (
    create_entropy_repositories,
    repo_setup,
    set_repo_user_config,
)

from .utils import check_subproc_run_for_nonzero


@pytest.fixture()
def jupyter_book_source() -> pathlib.Path:
    """
    Fixture for Jupyter Book content.
    """

    # return the location of the almanack content
    return pathlib.Path("src/book")


@pytest.fixture()
def build_jupyter_book(
    jupyter_book_source: str, tmp_path: pathlib.Path
) -> pathlib.Path:
    """
    Fixture to build Jupyter Book content.

    Note: we use the command line interface for Jupyter Book as this is
    well documented and may have alignment with development tasks.
    """

    # specify a source and target dir for jupyter book content with tests
    jupyter_book_test_source = pathlib.Path(tmp_path / "jupyter-book-test-source")
    jupyter_book_test_target = pathlib.Path(tmp_path / "jupyter-book-test-target")

    jupyter_book_test_target.mkdir()

    # copy the source and add development-only files for testing
    shutil.copytree(jupyter_book_source, jupyter_book_test_source)
    shutil.copy("tests/data/jupyter-book/sandbox.md", jupyter_book_test_source)
    with open(jupyter_book_test_source / "_toc.yml", "a") as tocfile:
        tocfile.write("      - file: sandbox.md")

    # build jupyter book content
    result = subprocess.run(
        [
            "jupyter-book",
            "build",
            jupyter_book_test_source,
            "--path-output",
            jupyter_book_test_target,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    check_subproc_run_for_nonzero(completed_proc=result)

    return jupyter_book_test_target


@pytest.fixture(scope="session")
def entropy_repository_paths(tmp_path_factory):
    """
    Fixture to call create_entropy_repositories, create the repositories, then delete them
    using the tmp_path_factory fixture to provide a temporary directory for tests.
    """
    # Create a base temporary directory
    base_path = tmp_path_factory.mktemp("almanack_entropy")

    # Run create_repositories with the base_path argument
    create_entropy_repositories(base_path)

    repositories = {
        "3_file_repo": base_path / "3_file_repo",
        "1_file_repo": base_path / "1_file_repo",
    }

    yield repositories


@pytest.fixture
def repo_file_sets():
    """
    Provides a mapping of test repository names to lists of file names.

    Returns:
        dict[str, list[str]]: A dictionary where the keys are repository names
        and the values are lists of file names in those repositories.
    """
    return {
        "3_file_repo": ["file_1.md", "file_2.md", "file_3.md"],
        "1_file_repo": ["file_1.md"],
    }


@pytest.fixture(scope="session")
def community_health_repository_path(tmp_path_factory):
    """
    Fixture to call create_community_health_repository, create the repositories, then delete them
    using the tmp_path_factory fixture to provide a temporary directory for tests.
    """

    # Create a temporary directory for the session
    temp_dir = tmp_path_factory.mktemp("community_health_repo")

    yield repo_setup(
        repo_path=pathlib.Path(temp_dir),
        files=[
            {
                "files": {
                    "README.md": "# This is an example readme\n\nWelcome to our repo!",
                    "CONTRIBUTING.md": "# This is a stub for a CONTRIBUTING.md",
                    "CODE_OF_CONDUCT.md": "# This is a stub for a CODE_OF_CONDUCT.md",
                    "LICENSE.txt": "This is an example LICENSE file.",
                }
            }
        ],
    )


@pytest.fixture
def repo_with_citation_in_readme(tmp_path):
    """Create a temporary repository with a specific structure for testing."""
    # Create a new repository in the temporary path
    repo = pygit2.init_repository(tmp_path, bare=False)

    # Set user.name and user.email in the config
    set_repo_user_config(repo)

    (tmp_path / "README.md").write_text("## Citation")

    index = repo.index

    index.add_all()
    index.write()

    author = repo.default_signature

    tree = repo.index.write_tree()

    repo.create_commit(
        "refs/heads/main",
        author,
        author,
        "Committing nested files",
        tree,
        [],
    )
    # set the head to the main branch
    repo.set_head("refs/heads/main")

    yield repo  # Provide the repository to the tests


@pytest.fixture
def current_repo():
    """
    Fixture to get the current repository being tested.
    """
    repo_path = pathlib.Path(".").resolve()
    return pygit2.Repository(str(repo_path))
