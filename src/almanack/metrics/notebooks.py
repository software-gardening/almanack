import logging
import pathlib
from dataclasses import dataclass
from typing import Dict, List, Union

import nbformat


@dataclass
class JupyterCell:
    """Data class representing a Jupyter notebook cell, containing
    information about its type and execution count.

    Attributes
    ----------
    cell_type : str
        The type of the Jupyter notebook cell (e.g., 'code', 'markdown').
    execution_count : Union[int, None]
        The execution count of the cell, indicating the order in which
        the code cells were run.
    """

    cell_type: str
    execution_count: Union[int, None]


def _create_jupyter_cell(cell: dict) -> JupyterCell:
    """
    Create a JupyterCell object from a notebook cell dictionary.

    Parameters
    ----------
    cell : dict
        Dictionary containing cell information from nbformat.

    Returns
    -------
    JupyterCell
        A JupyterCell object with cell type and execution count.
    """
    cell_type = cell["cell_type"]
    execution_count = cell.get("execution_count") if cell_type == "code" else None

    return JupyterCell(cell_type=cell_type, execution_count=execution_count)


def get_nb_contents(
    repo_path: Union[str, pathlib.Path],
    ignore_dirs: Union[List[str], None] = None,
) -> Dict[pathlib.Path, List[JupyterCell]]:
    """
    Loads the contents of all Jupyter notebooks in a repository and extracts cell information.

    Parameters
    ----------
    repo_path : Union[str, pathlib.Path]
        Path to the repository directory. Can be either a string or a pathlib.Path object.
    ignore_dirs : Union[List[str], None], optional
        List of directory names to ignore when searching for notebooks.
        If None, defaults to ignoring notebooks in 'tests' directories within 'almanack'.

    Returns
    -------
    Dict[pathlib.Path, List[JupyterCell]]
        A dictionary mapping notebook file paths to lists of JupyterCell objects,
        each representing a cell in the notebook with its type and execution count.
        For markdown cells, the execution count is set to None.

    Raises
    ------
    TypeError
        If repo_path is not a string or pathlib.Path object.
    FileNotFoundError
        If the specified path does not exist.
    """
    # Validate and normalize input path
    if not isinstance(repo_path, (str, pathlib.Path)):
        raise TypeError("repo_path must be a str or pathlib.Path")

    repo_path = pathlib.Path(repo_path)

    # Verify path exists
    if not repo_path.exists():
        raise FileNotFoundError(f"Repository path does not exist: {repo_path}")

    resolved_repo_path = repo_path.resolve()

    # Set default ignore directories
    if ignore_dirs is None:
        ignore_dirs = []

    # Find and process all notebook files in the repository
    notebook_contents = {}

    for notebook_file in resolved_repo_path.rglob("*.ipynb"):
        # Skip notebooks in ignored directories
        if any(ignored_dir in notebook_file.parts for ignored_dir in ignore_dirs):
            continue

        try:
            # Read notebook and extract cell metadata
            notebook = nbformat.read(notebook_file, as_version=4)
            cells = notebook.get("cells", [])

            # Create JupyterCell objects for each cell
            notebook_contents[notebook_file] = [
                _create_jupyter_cell(cell) for cell in cells
            ]
        # Handle potential file read errors
        except FileNotFoundError as e:
            logging.warning(f"Failed to process notebook {notebook_file}: {e}")
        except PermissionError as e:
            logging.warning(f"Permission denied for notebook {notebook_file}: {e}")
        except Exception as e:
            logging.warning(f"Failed to process notebook {notebook_file}: {e}")
            continue

    return notebook_contents


def check_ipynb_code_exec_order(nb_cells: List[JupyterCell]) -> bool:
    """
    Checks if code cells in a Jupyter notebook were executed in sequential order.

    This function extracts the execution counts from all code cells in the notebook.
    If any code cell has an execution count of None (indicating it was not executed),
    the function returns False. If there are no code cells or all code cells are
    unexecuted, it returns True. Otherwise, it checks if the execution counts form a
    consecutive sequence starting from 1 (i.e., [1, 2, 3, ...]).

    Parameters
    ----------
    nb_cells : List[JupyterCell]
        List of JupyterCell objects representing cells in the notebook.

    Returns
    -------
    bool
        True if code cells were executed in sequential order starting from 1 with no
        gaps or missing executions, False otherwise. Returns True for notebooks with
        no executed code cells.
    """
    # Extract execution counts from code cells, filtering out None values
    execution_counts = [
        cell.execution_count for cell in nb_cells if cell.cell_type == "code"
    ]

    # if there's a None in execution counts, return False
    # None can be ambiguous in code cells (sometimes means not executed)
    if any(count is None for count in execution_counts):
        return False

    # Empty list or no executed cells is considered valid
    if not execution_counts:
        return True

    # Check if execution counts form a consecutive sequence starting from 1
    expected_sequence = list(range(1, len(execution_counts) + 1))
    return execution_counts == expected_sequence
