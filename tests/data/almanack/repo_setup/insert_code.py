"""
This module introduces lines code to the test Markdown files by adding predefined lines of code.
"""

import pathlib


def write_lines(file_path: pathlib.Path, lines_of_code: str) -> None:
    """
    Adds lines of code to the specified file.

    Args:
        file_path (str): Path to the .md file.
        lines_of_code (str): List of lines of code to add.
    """
    with open(file_path, "w") as f:
        f.write(lines_of_code)


# Define the lines of code for each file
high_code_change = (
    """
\n
"""
    * 20
)
medium_code_change = (
    """
\n
"""
    * 10
)
low_code_change = (
    """
\n
"""
    * 5
)


def add_LOC(base_path: pathlib.Path) -> None:
    """
    Inserts lines of code (LOC) into specified files in the test repositories.

    Args:
        base_path (pathlib.Path): The base path where the test repositories are located.
    """
    entropy_levels = {
        base_path / "3_file_repo/file_1.md": high_code_change,
        base_path / "3_file_repo/file_2.md": medium_code_change,
        base_path / "3_file_repo/file_3.md": low_code_change,
        base_path / "1_file_repo/file_1.md": low_code_change,
    }
    # Add entropy to each file
    for file_path, lines_of_code in entropy_levels.items():
        write_lines(file_path, lines_of_code)
