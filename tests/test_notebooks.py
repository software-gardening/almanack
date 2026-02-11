"""
Tests for the notebooks module.

This module contains comprehensive tests for loading and analyzing Jupyter notebook contents,
including testing execution order validation and cell parsing functionality.

Test Data:
---------
- ordered-nb.ipynb: A notebook with code cells executed in sequential order (1, 2, 3, 4)
- unordered-nb.ipynb: A notebook with code cells executed out of order (1, 5, 3, 6)

These test notebooks are used to validate:
- Loading notebook contents from directories
- Parsing cell types and execution counts
- Detecting proper vs improper execution order
- Error handling for invalid inputs and corrupted files
"""

import pathlib
import tempfile
from unittest.mock import patch

import pytest

from almanack.git import repo_dir_exists
from almanack.metrics.notebooks import (
    JupyterCell,
    _create_jupyter_cell,
    check_ipynb_code_exec_order,
    get_nb_contents,
)

# Test constants
EXPECTED_TEST_NOTEBOOKS = 2
EXPECTED_NOTEBOOK_CELLS = 7


class TestJupyterCell:
    """Test the JupyterCell dataclass."""

    def test_jupyter_cell_creation(self):
        """Test creating a JupyterCell object."""
        cell = JupyterCell(cell_type="code", execution_count=1)
        assert cell.cell_type == "code"
        assert cell.execution_count == 1

    def test_jupyter_cell_markdown(self):
        """Test creating a markdown JupyterCell object."""
        cell = JupyterCell(cell_type="markdown", execution_count=None)
        assert cell.cell_type == "markdown"
        assert cell.execution_count is None


class TestCreateJupyterCell:
    """Test the _create_jupyter_cell helper function."""

    def test_create_code_cell(self):
        """Test creating a JupyterCell from a code cell dictionary."""
        test_execution_count = 5
        cell_dict = {
            "cell_type": "code",
            "execution_count": test_execution_count,
            "source": ["print('hello')"],
        }
        cell = _create_jupyter_cell(cell_dict)
        assert cell.cell_type == "code"
        assert cell.execution_count == test_execution_count

    def test_create_markdown_cell(self):
        """Test creating a JupyterCell from a markdown cell dictionary."""
        cell_dict = {"cell_type": "markdown", "source": ["# Title"]}
        cell = _create_jupyter_cell(cell_dict)
        assert cell.cell_type == "markdown"
        assert cell.execution_count is None

    def test_create_code_cell_no_execution(self):
        """Test creating a JupyterCell from an unexecuted code cell."""
        cell_dict = {
            "cell_type": "code",
            "execution_count": None,
            "source": ["print('hello')"],
        }
        cell = _create_jupyter_cell(cell_dict)
        assert cell.cell_type == "code"
        assert cell.execution_count is None


class TestRepoDirExists:
    """Test the repo_dir_exists function."""

    def test_existing_directory(self, current_repo):
        """Test with an existing directory."""
        assert repo_dir_exists(current_repo, "jupyter-book") is True

    def test_non_existing_directory(self, current_repo):
        """Test with a non-existing directory."""
        assert repo_dir_exists(current_repo, "non-existent-directory") is False

    def test_existing_nested_directory(self, current_repo):
        """Test with an existing nested directory."""
        assert repo_dir_exists(current_repo, "data") is True


class TestGetNbContents:
    """Test the get_nb_contents function."""

    @pytest.fixture
    def test_data_dir(self):
        """Fixture providing the test data directory path."""
        return pathlib.Path(__file__).parent / "data" / "jupyter-book"

    def test_load_notebooks_from_directory(self, test_data_dir):
        """Test loading notebooks from a directory."""
        result = get_nb_contents(test_data_dir)

        # Should find both test notebooks
        assert len(result) == EXPECTED_TEST_NOTEBOOKS

        # Check that we have the expected notebook files
        notebook_names = {path.name for path in result.keys()}
        assert "ordered-nb.ipynb" in notebook_names
        assert "unordered-nb.ipynb" in notebook_names

    def test_load_ordered_notebook_structure(self, test_data_dir):
        """Test the structure of the ordered notebook."""
        result = get_nb_contents(test_data_dir)

        # Find the ordered notebook
        ordered_nb_path = None
        for path in result.keys():
            if path.name == "ordered-nb.ipynb":
                ordered_nb_path = path
                break

        assert ordered_nb_path is not None
        cells = result[ordered_nb_path]

        # Should have 7 cells total
        assert len(cells) == EXPECTED_NOTEBOOK_CELLS

        # Check cell types and execution counts
        expected_cells = [
            ("markdown", None),
            ("code", 1),
            ("code", 2),
            ("markdown", None),
            ("code", 3),
            ("markdown", None),
            ("code", 4),
        ]

        for i, (expected_type, expected_count) in enumerate(expected_cells):
            assert cells[i].cell_type == expected_type
            assert cells[i].execution_count == expected_count

    def test_load_unordered_notebook_structure(self, test_data_dir):
        """Test the structure of the unordered notebook."""
        result = get_nb_contents(test_data_dir)

        # Find the unordered notebook
        unordered_nb_path = None
        for path in result.keys():
            if path.name == "unordered-nb.ipynb":
                unordered_nb_path = path
                break

        assert unordered_nb_path is not None
        cells = result[unordered_nb_path]

        # Should have 7 cells total
        assert len(cells) == EXPECTED_NOTEBOOK_CELLS

        # Check cell types and execution counts for unordered notebook
        expected_cells = [
            ("markdown", None),
            ("code", 1),
            ("code", 5),  # Out of order execution
            ("markdown", None),
            ("code", 3),  # Out of order execution
            ("markdown", None),
            ("code", 6),  # Out of order execution
        ]

        for i, (expected_type, expected_count) in enumerate(expected_cells):
            assert cells[i].cell_type == expected_type
            assert cells[i].execution_count == expected_count

    def test_non_existing_path(self):
        """Test with a non-existing path."""
        with pytest.raises(FileNotFoundError, match="Repository path does not exist"):
            get_nb_contents("/non/existent/path")

    def test_invalid_input_type(self):
        """Test with invalid input type."""
        with pytest.raises(
            TypeError, match=r"repo_path must be a str or pathlib\.Path"
        ):
            get_nb_contents(123)

    def test_empty_directory(self):
        """Test with an empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = get_nb_contents(temp_dir)
            assert result == {}

    def test_string_path_input(self, test_data_dir):
        """Test with string path input."""
        result = get_nb_contents(str(test_data_dir))
        assert len(result) == EXPECTED_TEST_NOTEBOOKS

    @patch("almanack.metrics.notebooks.json.load")
    @patch("almanack.metrics.notebooks.logging.warning")
    def test_error_handling_corrupt_notebook(
        self, mock_warning, mock_json_load, test_data_dir
    ):
        """Test error handling when a notebook file is corrupted."""
        # Mock json.load to raise an exception
        mock_json_load.side_effect = Exception("Corrupted notebook file")

        result = get_nb_contents(test_data_dir)

        # Should return empty dict when all notebooks fail to load
        assert result == {}

        # Should have logged warnings for failed notebooks
        assert mock_warning.call_count > 0


class TestCheckNbCodeExecOrder:
    """Test the check_nb_code_exec_order function."""

    def test_ordered_execution(self):
        """Test with properly ordered execution counts."""
        cells = [
            JupyterCell("markdown", None),
            JupyterCell("code", 1),
            JupyterCell("code", 2),
            JupyterCell("markdown", None),
            JupyterCell("code", 3),
            JupyterCell("code", 4),
        ]
        assert check_ipynb_code_exec_order(cells) is True

    def test_unordered_execution(self):
        """Test with unordered execution counts."""
        cells = [
            JupyterCell("markdown", None),
            JupyterCell("code", 1),
            JupyterCell("code", 5),  # Out of order
            JupyterCell("markdown", None),
            JupyterCell("code", 3),  # Out of order
            JupyterCell("code", 6),
        ]
        assert check_ipynb_code_exec_order(cells) is False

    def test_no_code_cells(self):
        """Test with no code cells."""
        cells = [
            JupyterCell("markdown", None),
            JupyterCell("markdown", None),
        ]
        assert check_ipynb_code_exec_order(cells) is True

    def test_no_executed_code_cells(self):
        """Test with code cells that haven't been executed (None execution counts)."""
        cells = [
            JupyterCell("markdown", None),
            JupyterCell("code", None),
            JupyterCell("code", None),
        ]
        # None execution counts indicate unexecuted cells, which returns False
        assert check_ipynb_code_exec_order(cells) is False

    def test_mixed_executed_unexecuted_cells(self):
        """Test with mix of executed and unexecuted code cells."""
        cells = [
            JupyterCell("code", 1),
            JupyterCell("code", None),  # Unexecuted
            JupyterCell("code", 2),
        ]
        # Any None execution count causes the function to return False
        assert check_ipynb_code_exec_order(cells) is False

    def test_empty_cell_list(self):
        """Test with empty cell list."""
        assert check_ipynb_code_exec_order([]) is True

    def test_single_code_cell(self):
        """Test with single executed code cell."""
        cells = [JupyterCell("code", 1)]
        assert check_ipynb_code_exec_order(cells) is True

    def test_single_code_cell_wrong_start(self):
        """Test with single code cell not starting at 1."""
        cells = [JupyterCell("code", 5)]
        assert check_ipynb_code_exec_order(cells) is False

    def test_gap_in_execution_sequence(self):
        """Test with gap in execution sequence."""
        cells = [
            JupyterCell("code", 1),
            JupyterCell("code", 2),
            JupyterCell("code", 4),  # Gap: missing 3
        ]
        assert check_ipynb_code_exec_order(cells) is False


class TestIntegrationTests:
    """Integration tests combining multiple functions."""

    @pytest.fixture
    def test_data_dir(self):
        """Fixture providing the test data directory path."""
        return pathlib.Path(__file__).parent / "data" / "jupyter-book"

    def test_ordered_notebook_integration(self, test_data_dir):
        """Test full workflow with ordered notebook."""
        result = get_nb_contents(test_data_dir)

        # Find ordered notebook
        ordered_nb_path = None
        for path in result.keys():
            if path.name == "ordered-nb.ipynb":
                ordered_nb_path = path
                break

        assert ordered_nb_path is not None
        cells = result[ordered_nb_path]

        # Should be properly ordered
        assert check_ipynb_code_exec_order(cells) is True

    def test_unordered_notebook_integration(self, test_data_dir):
        """Test full workflow with unordered notebook."""
        result = get_nb_contents(test_data_dir)

        # Find unordered notebook
        unordered_nb_path = None
        for path in result.keys():
            if path.name == "unordered-nb.ipynb":
                unordered_nb_path = path
                break

        assert unordered_nb_path is not None
        cells = result[unordered_nb_path]

        # Should be improperly ordered
        assert check_ipynb_code_exec_order(cells) is False

    def test_directory_validation_integration(self, test_data_dir, current_repo):
        """Test directory validation before processing."""
        # Valid directory should work
        assert repo_dir_exists(current_repo, "jupyter-book") is True
        result = get_nb_contents(test_data_dir)
        assert len(result) == EXPECTED_TEST_NOTEBOOKS

        # Invalid directory should fail validation
        assert repo_dir_exists(current_repo, "non-existent-directory") is False
        with pytest.raises(FileNotFoundError):
            get_nb_contents("/definitely/does/not/exist")
