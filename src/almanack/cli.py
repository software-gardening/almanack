"""
Setup Entropy Report CLI through python-fire
"""

import fire

from .metrics.data import get_table

def cli_get_table() -> None:
    """
    Run the CLI command to process `report.py` using python-fire.
    """
    fire.Fire(get_table)

if __name__ == "__main__":
    """
    Setup the CLI with python-fire for the almanack package.

    This allows the function `check` to be ran through the
    command line interface.
    """
    cli_get_table()
