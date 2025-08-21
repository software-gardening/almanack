import logging
import pathlib
from dataclasses import dataclass

import nbformat


@dataclass
class JupyterCell:
    """Data class representing a Jupyter notebook cell, containing
    information about its type and execution count.

    Attributes
    ----------
    cell_type : str
        The type of the Jupyter notebook cell (e.g., 'code', 'markdown').
    execution_count : int | None
        The execution count of the cell, indicating the order in which
        the code cells were run.
    """

    cell_type: str
    execution_count: int | None


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
    repo_path: str | pathlib.Path,
) -> dict[pathlib.Path, list[JupyterCell]]:
    """
    Loads the contents of all Jupyter notebooks in a repository and extracts cell information.

    Parameters
    ----------
    repo_path : str | pathlib.Path
        Path to the repository directory. Can be either a string or a pathlib.Path object.
    ignore_md : bool, optional
        Whether to ignore markdown cells. Default is True.

    Returns
    -------
    dict[pathlib.Path, list[JupyterCell]]
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

    # Find and process all notebook files in the repository
    notebook_contents = {}

    for notebook_file in resolved_repo_path.rglob("*.ipynb"):
        try:
            # Read notebook and extract cell metadata
            notebook = nbformat.read(notebook_file, as_version=4)
            cells = notebook.get("cells", [])

            # Create JupyterCell objects for each cell
            notebook_contents[notebook_file] = [
                _create_jupyter_cell(cell) for cell in cells
            ]
        except Exception as e:
            # Log error but continue processing other notebooks
            logging.warning(f"Failed to read notebook {notebook_file}: {e}")
            continue

    return notebook_contents


def check_nb_code_exec_order(nb_cells: list[JupyterCell]) -> bool:
    """
    Checks if code cells in a Jupyter notebook were executed in sequential order.

    Verifies that the execution counts of code cells form a consecutive sequence
    starting from 1, indicating the notebook was executed from top to bottom
    without re-running cells out of order.

    Parameters
    ----------
    nb_cells : list[JupyterCell]
        List of JupyterCell objects representing cells in the notebook.

    Returns
    -------
    bool
        True if code cells were executed in sequential order (1, 2, 3, ...),
        False otherwise. Returns True for notebooks with no executed code cells.
    """
    # Extract execution counts from code cells, filtering out None values
    execution_counts = [
        cell.execution_count
        for cell in nb_cells
        if cell.cell_type == "code" and cell.execution_count is not None
    ]

    # Empty list or no executed cells is considered valid
    if not execution_counts:
        return True

    # Check if execution counts form a consecutive sequence starting from 1
    expected_sequence = list(range(1, len(execution_counts) + 1))
    return execution_counts == expected_sequence


def notebook_dir_exists(repo_path: str | pathlib.Path) -> bool:
    """
    Check if the specified path exists and is a directory.

    Parameters
    ----------
    repo_path : str | pathlib.Path
        Path to check. Can be either a string or a pathlib.Path object.

    Returns
    -------
    bool
        True if the path exists and is a directory, False otherwise.

    Raises
    ------
    TypeError
        If repo_path is not a string or pathlib.Path object.
    """
    if not isinstance(repo_path, (str, pathlib.Path)):
        raise TypeError("repo_path must be a str or pathlib.Path")

    repo_path = pathlib.Path(repo_path)
    return repo_path.exists() and repo_path.is_dir()
