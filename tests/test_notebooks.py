"""
Tests for the notebooks module.

This module contains comprehensive tests for loading and analyzing Jupyter notebook contents,
including testing execution order validation, import statement placement, and cell parsing functionality.

Test Data:
---------
Execution Order Tests:
- ordered-nb.ipynb: A notebook with code cells executed in sequential order (1, 2, 3, 4)
- unordered-nb.ipynb: A notebook with code cells executed out of order (1, 5, 3, 6)

Import Statement Tests:
- pass-imports-first-cell.ipynb: All imports in first code cell (PASS)
- fail-imports-scattered.ipynb: Imports scattered across multiple cells (FAIL)
- pass-no-imports.ipynb: No imports at all (PASS)
- fail-imports-not-first.ipynb: First cell has no imports, later cells do (FAIL)
- pass-only-markdown.ipynb: Only markdown cells, no code cells (PASS)
- pass-imports-with-magic.ipynb: Imports with IPython magic commands (PASS)
- pass-imports-with-docstrings-comments.ipynb: Word 'import' in docstrings/comments (PASS)

These test notebooks are used to validate:
- Loading notebook contents from directories
- Parsing cell types and execution counts
- Detecting proper vs improper execution order
- Checking import statement placement following PEP 8 guidelines
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
    _has_imports_in_cell,
    check_ipynb_code_exec_order,
    check_ipynb_imports_calls,
    get_nb_contents,
)

# Test constants
EXPECTED_TEST_NOTEBOOKS = 10  # Updated to include new import test notebooks
EXPECTED_NOTEBOOK_CELLS = 7


class TestJupyterCell:
    """Test the JupyterCell dataclass."""

    def test_jupyter_cell_creation(self):
        """Test creating a JupyterCell object."""
        cell = JupyterCell(cell_type="code", execution_count=1, source="print('hello')")
        assert cell.cell_type == "code"
        assert cell.execution_count == 1

    def test_jupyter_cell_markdown(self):
        """Test creating a markdown JupyterCell object."""
        cell = JupyterCell(cell_type="markdown", execution_count=None, source="# Title")
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

    @patch("almanack.metrics.notebooks.nbformat.read")
    @patch("almanack.metrics.notebooks.logging.warning")
    def test_error_handling_corrupt_notebook(
        self, mock_warning, mock_read, test_data_dir
    ):
        """Test error handling when a notebook file is corrupted."""
        # Mock nbformat.read to raise an exception
        mock_read.side_effect = Exception("Corrupted notebook file")

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
            JupyterCell("markdown", None, "# Title"),
            JupyterCell("code", 1, "x = 1"),
            JupyterCell("code", 2, "y = 2"),
            JupyterCell("markdown", None, "## Section"),
            JupyterCell("code", 3, "z = 3"),
            JupyterCell("code", 4, "w = 4"),
        ]
        assert check_ipynb_code_exec_order(cells) is True

    def test_unordered_execution(self):
        """Test with unordered execution counts."""
        cells = [
            JupyterCell("markdown", None, "# Title"),
            JupyterCell("code", 1, "x = 1"),
            JupyterCell("code", 5, "y = 5"),  # Out of order
            JupyterCell("markdown", None, "## Section"),
            JupyterCell("code", 3, "z = 3"),  # Out of order
            JupyterCell("code", 6, "w = 6"),
        ]
        assert check_ipynb_code_exec_order(cells) is False

    def test_no_code_cells(self):
        """Test with no code cells."""
        cells = [
            JupyterCell("markdown", None, "# Title"),
            JupyterCell("markdown", None, "## Section"),
        ]
        assert check_ipynb_code_exec_order(cells) is True

    def test_no_executed_code_cells(self):
        """Test with code cells that haven't been executed (None execution counts)."""
        cells = [
            JupyterCell("markdown", None, "# Title"),
            JupyterCell("code", None, "x = 1"),
            JupyterCell("code", None, "y = 2"),
        ]
        # None execution counts indicate unexecuted cells, which returns False
        assert check_ipynb_code_exec_order(cells) is False

    def test_mixed_executed_unexecuted_cells(self):
        """Test with mix of executed and unexecuted code cells."""
        cells = [
            JupyterCell("code", 1, "x = 1"),
            JupyterCell("code", None, "y = 2"),  # Unexecuted
            JupyterCell("code", 2, "z = 3"),
        ]
        # Any None execution count causes the function to return False
        assert check_ipynb_code_exec_order(cells) is False

    def test_empty_cell_list(self):
        """Test with empty cell list."""
        assert check_ipynb_code_exec_order([]) is True

    def test_single_code_cell(self):
        """Test with single executed code cell."""
        cells = [JupyterCell("code", 1, "x = 1")]
        assert check_ipynb_code_exec_order(cells) is True

    def test_single_code_cell_wrong_start(self):
        """Test with single code cell not starting at 1."""
        cells = [JupyterCell("code", 5, "x = 1")]
        assert check_ipynb_code_exec_order(cells) is False

    def test_gap_in_execution_sequence(self):
        """Test with gap in execution sequence."""
        cells = [
            JupyterCell("code", 1, "x = 1"),
            JupyterCell("code", 2, "y = 2"),
            JupyterCell("code", 4, "z = 4"),  # Gap: missing 3
        ]
        assert check_ipynb_code_exec_order(cells) is False


class TestHasImportsInCell:
    """Test the _has_imports_in_cell helper function."""

    def test_simple_import(self):
        """Test detection of simple import statement."""
        assert _has_imports_in_cell("import numpy as np") is True

    def test_from_import(self):
        """Test detection of from...import statement."""
        assert _has_imports_in_cell("from typing import List, Dict") is True

    def test_multiple_imports(self):
        """Test detection of multiple import statements."""
        source = "import numpy as np\nimport pandas as pd\nfrom typing import List"
        assert _has_imports_in_cell(source) is True

    def test_no_imports(self):
        """Test cell with no imports."""
        assert _has_imports_in_cell("x = 5\ny = 10\nresult = x + y") is False

    def test_commented_import(self):
        """Test that commented imports are not detected."""
        assert _has_imports_in_cell("# import numpy as np") is False

    def test_import_in_string(self):
        """Test that imports in strings are detected (AST limitation)."""
        # AST will not detect this as an import statement
        source = 'my_string = "import numpy as np"'
        assert _has_imports_in_cell(source) is False

    def test_ipython_magic_with_import(self):
        """Test detection of imports with IPython magic commands."""
        source = "%matplotlib inline\nimport pandas as pd"
        assert _has_imports_in_cell(source) is True

    def test_import_with_docstring(self):
        """Test detection of imports with docstrings."""
        source = '"""This is a docstring"""\nimport numpy as np'
        assert _has_imports_in_cell(source) is True

    def test_only_docstring(self):
        """Test cell with only docstring, no imports."""
        source = '"""This is just a docstring\nWith multiple lines"""'
        assert _has_imports_in_cell(source) is False

    def test_incomplete_code_with_import(self):
        """Test fallback for incomplete code containing imports."""
        source = "if True\n    import numpy as np"  # Syntax error
        # Falls back to heuristic which should detect this
        assert _has_imports_in_cell(source) is True


class TestCheckIpynbImportsCalls:
    """Test the check_ipynb_imports_calls function using actual test notebooks."""

    @pytest.fixture
    def test_data_dir(self):
        """Fixture providing the test data directory path."""
        return pathlib.Path(__file__).parent / "data" / "jupyter-book"

    @pytest.fixture
    def notebook_cells(self, test_data_dir):
        """Fixture that loads all test notebooks and returns their cells."""
        return get_nb_contents(test_data_dir)

    def _get_cells_by_filename(self, notebook_cells, filename):
        """Helper to get cells from a specific notebook by filename."""
        for path, cells in notebook_cells.items():
            if path.name == filename:
                return cells
        return None

    def test_imports_in_first_cell_only(self, notebook_cells):
        """Test notebook with all imports in first code cell (should pass)."""
        cells = self._get_cells_by_filename(notebook_cells, "pass-imports-first-cell.ipynb")
        assert cells is not None, "Test notebook not found"
        assert check_ipynb_imports_calls(cells) is True

    def test_imports_scattered(self, notebook_cells):
        """Test notebook with imports in multiple cells (should fail)."""
        cells = self._get_cells_by_filename(notebook_cells, "fail-imports-scattered.ipynb")
        assert cells is not None, "Test notebook not found"
        assert check_ipynb_imports_calls(cells) is False

    def test_no_imports(self, notebook_cells):
        """Test notebook with no imports (should pass)."""
        cells = self._get_cells_by_filename(notebook_cells, "pass-no-imports.ipynb")
        assert cells is not None, "Test notebook not found"
        assert check_ipynb_imports_calls(cells) is True

    def test_imports_not_in_first_cell(self, notebook_cells):
        """Test notebook where first cell has no imports but later cells do (should fail)."""
        cells = self._get_cells_by_filename(notebook_cells, "fail-imports-not-first.ipynb")
        assert cells is not None, "Test notebook not found"
        assert check_ipynb_imports_calls(cells) is False

    def test_only_markdown_cells(self, notebook_cells):
        """Test notebook with only markdown cells (should pass)."""
        cells = self._get_cells_by_filename(notebook_cells, "pass-only-markdown.ipynb")
        assert cells is not None, "Test notebook not found"
        assert check_ipynb_imports_calls(cells) is True

    def test_empty_notebook(self):
        """Test empty notebook (should pass)."""
        assert check_ipynb_imports_calls([]) is True

    def test_ipython_magic_with_imports_first_cell(self, notebook_cells):
        """Test that IPython magic commands with imports in first cell pass."""
        cells = self._get_cells_by_filename(notebook_cells, "pass-imports-with-magic.ipynb")
        assert cells is not None, "Test notebook not found"
        assert check_ipynb_imports_calls(cells) is True

    def test_ordered_notebook_imports(self, notebook_cells):
        """Test that the ordered execution notebook also has proper import placement."""
        cells = self._get_cells_by_filename(notebook_cells, "ordered-nb.ipynb")
        assert cells is not None, "Test notebook not found"
        # ordered-nb has imports in first code cell
        assert check_ipynb_imports_calls(cells) is True

    def test_unordered_notebook_imports(self, notebook_cells):
        """Test that the unordered execution notebook also has proper import placement."""
        cells = self._get_cells_by_filename(notebook_cells, "unordered-nb.ipynb")
        assert cells is not None, "Test notebook not found"
        # unordered-nb has imports in first code cell
        assert check_ipynb_imports_calls(cells) is True


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

    def test_imports_with_docstrings_comments_integration(self, test_data_dir):
        """Test notebook with imports in docstrings/comments but actual imports in first cell."""
        result = get_nb_contents(test_data_dir)

        # Find pass-imports-with-docstrings-comments notebook
        target_nb_path = None
        for path in result.keys():
            if path.name == "pass-imports-with-docstrings-comments.ipynb":
                target_nb_path = path
                break

        assert target_nb_path is not None, "Test notebook not found"
        cells = result[target_nb_path]

        # Should pass - word 'import' in docstrings/comments is not an actual import
        assert check_ipynb_imports_calls(cells) is True
        
        # Verify the cells contain the word 'import' in non-import contexts
        # Check that first code cell has docstring with 'import' in it
        code_cells = [cell for cell in cells if cell.cell_type == "code"]
        assert len(code_cells) > 0, "Should have code cells"
        
        # First code cell should have actual imports plus docstring mentioning 'import'
        first_code_cell = code_cells[0]
        assert "import" in first_code_cell.source.lower(), "First cell should contain 'import'"
        assert "import numpy" in first_code_cell.source, "Should have actual import statement"
        
        # Later cells should have 'import' in comments/docstrings but not as statements
        if len(code_cells) > 1:
            later_cells_combined = "\n".join(cell.source for cell in code_cells[1:])
            assert "import" in later_cells_combined.lower(), "Later cells should mention 'import' in comments/docstrings"
