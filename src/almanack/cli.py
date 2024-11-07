"""
Setup almanack CLI through python-fire
"""

import json

import fire

from .metrics.data import get_table


def cli_get_table() -> None:
    """
    Creates Fire CLI for get_table_json_wrapper.

    This enables the use of CLI such as:
    `almanck <repo path>`
    """
    fire.Fire(component=get_table, serialize=json.dumps)


if __name__ == "__main__":
    """
    Setup the CLI with python-fire for the almanack package.

    This allows the function `check` to be ran through the
    command line interface.
    """
    cli_get_table()
