import fnmatch
import json
import logging
import pathlib
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Union


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
        Dictionary containing notebook cell information from notebook JSON.

    Returns
    -------
    JupyterCell
        A JupyterCell object with cell type and execution count.
    """
    cell_type = cell["cell_type"]
    execution_count = cell.get("execution_count") if cell_type == "code" else None

    return JupyterCell(cell_type=cell_type, execution_count=execution_count)


@dataclass
class NotebookIgnoreMatchers:
    """Prepared matchers for notebook ignore checks.

    Attributes:
        ignore_globs: Glob patterns relative to the repository root.
        ignore_rel_prefixes: Repository-relative path prefixes to ignore.
        ignore_abs_paths: Absolute paths to ignore.
    """

    ignore_globs: List[str]
    ignore_rel_prefixes: List[str]
    ignore_abs_paths: List[pathlib.Path]


def _prepare_ignore_matchers(
    ignore_paths: Optional[Sequence[str]],
) -> NotebookIgnoreMatchers:
    """Prepare ignore matchers for notebook discovery.

    Args:
        ignore_paths: Repository-relative paths or glob patterns to ignore.
            Paths can point to files or directories.

    Returns:
        A NotebookIgnoreMatchers instance with prepared patterns.
    """
    if isinstance(ignore_paths, str):
        ignore_paths = [value.strip() for value in ignore_paths.split(",")]
    if not ignore_paths:
        return NotebookIgnoreMatchers(
            ignore_globs=[],
            ignore_rel_prefixes=[],
            ignore_abs_paths=[],
        )

    ignore_globs: List[str] = []
    ignore_rel_prefixes: List[str] = []
    ignore_abs_paths: List[pathlib.Path] = []

    for ignore_path in ignore_paths:
        if not ignore_path:
            continue
        if any(char in ignore_path for char in "*?[]"):
            ignore_globs.append(ignore_path.lstrip("./"))
            continue

        ignore_path_obj = pathlib.Path(ignore_path)
        if ignore_path_obj.is_absolute():
            ignore_abs_paths.append(ignore_path_obj)
        else:
            ignore_rel_prefixes.append(ignore_path_obj.as_posix().strip("/"))

    return NotebookIgnoreMatchers(
        ignore_globs=ignore_globs,
        ignore_rel_prefixes=ignore_rel_prefixes,
        ignore_abs_paths=ignore_abs_paths,
    )


def _should_ignore_notebook(
    notebook_file: pathlib.Path,
    resolved_repo_path: pathlib.Path,
    ignore_dirs: Sequence[str],
    ignore_matchers: NotebookIgnoreMatchers,
) -> bool:
    """Determine whether a notebook should be ignored.

    Args:
        notebook_file: Path to the notebook file.
        resolved_repo_path: Absolute repository root.
        ignore_dirs: Directory names to ignore.
        ignore_matchers: Prepared ignore matchers.

    Returns:
        True if the notebook should be ignored, False otherwise.
    """
    rel_path = notebook_file.relative_to(resolved_repo_path).as_posix()

    if any(ignored_dir in notebook_file.parts for ignored_dir in ignore_dirs):
        return True
    if any(
        fnmatch.fnmatch(rel_path, pattern) for pattern in ignore_matchers.ignore_globs
    ):
        return True
    if any(
        rel_path == prefix or rel_path.startswith(f"{prefix}/")
        for prefix in ignore_matchers.ignore_rel_prefixes
    ):
        return True
    if ignore_matchers.ignore_abs_paths:
        notebook_resolved = notebook_file.resolve()
        if any(
            notebook_resolved == ignore_abs_path
            or ignore_abs_path in notebook_resolved.parents
            for ignore_abs_path in ignore_matchers.ignore_abs_paths
        ):
            return True

    return False


def get_nb_contents(
    repo_path: Union[str, pathlib.Path],
    ignore_dirs: Union[List[str], None] = None,
    ignore_paths: Union[List[str], None] = None,
) -> Dict[pathlib.Path, List[JupyterCell]]:
    """Load notebook contents and extract cell information.

    Args:
        repo_path: Path to the repository directory.
        ignore_dirs: Directory names to ignore when searching for notebooks.
            Defaults to none when not provided.
        ignore_paths: Repository-relative paths or glob patterns to ignore.
            Paths can point to files or directories.

    Returns:
        A mapping of notebook file paths to lists of JupyterCell objects. Markdown
        cells have execution_count set to None.

    Raises:
        TypeError: If repo_path is not a str or pathlib.Path.
        FileNotFoundError: If the specified path does not exist.
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

    if ignore_paths is None:
        ignore_paths = []

    ignore_matchers = _prepare_ignore_matchers(ignore_paths=ignore_paths)

    # Find and process all notebook files in the repository
    notebook_contents = {}

    for notebook_file in resolved_repo_path.rglob("*.ipynb"):
        if _should_ignore_notebook(
            notebook_file=notebook_file,
            resolved_repo_path=resolved_repo_path,
            ignore_dirs=ignore_dirs,
            ignore_matchers=ignore_matchers,
        ):
            continue

        try:
            # Parse raw notebook JSON and only extract fields needed for metrics.
            with notebook_file.open(encoding="utf-8") as notebook_json:
                notebook = json.load(notebook_json)
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
