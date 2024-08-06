"""
Setup Entropy Report CLI through python-fire
"""

import fire

import almanack.processing.processing_repositories as proc


def trigger() -> None:
    """
    Run the CLI command to process `report.py` using python-fire.
    """
    fire.Fire(proc)


if __name__ == "__main__":
    """
    Setup the CLI with python-fire for the almanack package.

    This allows the function `check` to be ran through the
    command line interface.
    """
    trigger()
