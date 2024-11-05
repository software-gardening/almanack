"""
Setup almanack CLI through python-fire
"""

import json

import fire

from .metrics.data import get_table


def get_table_json_wrapper(repo_path: str) -> str:
    """
    Converts the output of get_table to a proper JSON str.
    Note: python-fire seems to convert lists of dictionaries
    into individual dictionaries without distinction within list.

    Args:
        repo_path (str):
            Path to the repository from which to retrieve and
            convert the table data.

    Returns:
        str:
            JSON string representation of the table data.
    """

    return json.dumps(get_table(repo_path=repo_path))


def cli_get_table() -> None:
    """
    Creates Fire CLI for get_table_json_wrapper.

    This enables the use of CLI such as:
    `almanck <repo path>`
    """
    fire.Fire(get_table_json_wrapper)


if __name__ == "__main__":
    """
    Setup the CLI with python-fire for the almanack package.

    This allows the function `check` to be ran through the
    command line interface.
    """
    cli_get_table()
