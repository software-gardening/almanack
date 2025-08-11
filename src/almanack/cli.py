"""
Setup almanack CLI through python-fire
"""

import json
import shutil
import sys
from datetime import datetime, timezone
from typing import List, Optional

import fire
from tabulate import tabulate

from almanack.metrics.data import (
    _get_almanack_version,
    gather_failed_almanack_metric_checks,
    get_table,
)


def cli_link(uri: str, label: Optional[str] = None, parameters: str = ""):
    """
    Create a CLI-based link for a given URI.

    Referenced with modifications from:
    https://stackoverflow.com/a/71309268

    Args:
        uri (str):
            The URI to link to.
        label (str, optional):
            The label for the link. Defaults to None.

    Returns:
        str:
            An OSC 8 escape sequence for the link.
    """
    # if we have no label, use the URI as the label
    if label is None:
        label = uri

    # formatted string with order:
    # OSC 8 ; params ; URI ST <name> OSC 8 ;; ST
    return f"\033]8;{parameters};{uri}\033\\{label}\033]8;;\033\\"


class AlmanackCLI(object):
    """
    Almanack CLI class for Google Fire

    The following CLI-based commands are available
    (and in alignment with the methods below based
    on their name):

    - `almanack table <repo path>`: Provides a JSON data
        structure which includes Almanack metric data.
        Always returns a 0 exit.
    - `almanack check <repo path>`: Provides a report
        of boolean metrics which include a non-zero
        sustainability direction ("checks") that are
        failing to inform a user whether they pass.
        Returns non-zero exit (1) if any checks are failing,
        otherwise 0.
    """

    def table(
        self,
        repo_path: str,
        dest_path: Optional[str] = None,
        ignore: Optional[List[str]] = None,
        verbose: bool = False,
    ) -> None:
        """
        Used through CLI to
        generate a table of metrics

        This enables the use of CLI such as:
        `almanack table <repo path>`

        Args:
            repo_path (str):
                The path to the repository to analyze.
            dest_path (str):
                A path to send the output to.
            ignore (List[str]):
                A list of metric IDs to ignore when
                running the checks. Defaults to None.
             verbose (bool):
                If True, print extra information.
        """

        if verbose:
            print(  # noqa: T201
                f"Gathering table for repo: {repo_path} (ignore={ignore})"
            )

        # serialized JSON as a string
        json_output = json.dumps(
            # gather table data from Almanack
            get_table(repo_path=repo_path, ignore=ignore),
        )

        # if we have a dest_path, send data to file
        if dest_path is not None:
            with open(dest_path, "w") as f:
                f.write(json_output)
            print(f"Wrote data to file: {dest_path}")  # noqa: T201

        # otherwise use stdout
        else:
            print(json_output)  # noqa: T201

        # exit with zero status for no errors
        # (we don't check for failures with this
        # CLI option.)
        sys.exit(0)

    def check(
        self, repo_path: str, ignore: Optional[List[str]] = None, verbose: bool = False
    ) -> None:
        """
        Used through CLI to
        check table of metrics for
        boolean values with a non-zero
        sustainability direction
        for failures.

        This enables the use of CLI such as:
        `almanack check <repo path>`

        Args:
            repo_path (str):
                The path to the repository to analyze.
            ignore (List[str]):
                A list of metric IDs to ignore when
                running the checks. Defaults to None.
        """

        # header for CLI output
        datetime_now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        print(  # noqa: T201
            "Running Software Gardening Almanack checks.",
            f"Datetime: {datetime_now}",
            f"Almanack version: {_get_almanack_version()}",
            f"Target repository path: {repo_path}",
            sep="\n",
        )

        if verbose:
            print(f"Running check on repo: {repo_path} (ignore={ignore})")  # noqa: T201

        # gather failed metrics
        failed_metrics = gather_failed_almanack_metric_checks(
            repo_path=repo_path, ignore=ignore
        )

        # gather almanack score metrics
        almanack_score_metrics = next(
            (
                metric["result"]
                for metric in failed_metrics
                if metric["name"] == "repo-almanack-score"
            ),
            None,
        )

        # prepare almanack score output
        almanack_score_output = (
            f"Software Gardening Almanack summary: {100 * almanack_score_metrics['almanack-score']:.2f}% "
            f"({almanack_score_metrics['almanack-score-numerator']}/"
            f"{almanack_score_metrics['almanack-score-denominator']})"
        )

        # if we have under 1 almanack score, we have failures
        # and show the guidance for those failures with a
        # non-zero exit.
        if almanack_score_metrics["almanack-score"] != 1:

            # introduce a table of output in CLI
            print(  # noqa: T201
                "The following Software Gardening Almanack metrics may be helpful to improve your repository:"
            )

            # Format the output
            failures_output_table = [
                [
                    metric["id"],
                    metric["name"],
                    metric["correction_guidance"],
                    cli_link(
                        uri=f"https://software-gardening.github.io/almanack/checks/{metric['id']}.html",
                        label="link",
                    ),
                ]
                for metric in failed_metrics
                if metric["name"] != "repo-almanack-score"
            ]

            # gather the max length of the ID and Name columns for use in formatting below
            max_id_length = max(len(metric[0]) for metric in failures_output_table)
            max_name_length = max(len(metric[1]) for metric in failures_output_table)

            # calculate the max width for the guidance column in output
            max_width = (shutil.get_terminal_size().columns) - (
                max_id_length + max_name_length + 25
            )

            # show a table of failures
            print(  # noqa: T201
                str(
                    tabulate(
                        tabular_data=failures_output_table,
                        headers=["ID", "Name", "Guidance", "More Info"],
                        tablefmt="rounded_grid",
                        # set a dynamic width for each column in the table
                        # where the None is no max width and the final column
                        # is a dynamic max width of the terminal minus the other
                        # column lengths.
                        maxcolwidths=[
                            None,
                            None,
                            max_width if max_width > 0 else 30,
                            None,
                        ],
                    )
                )
            )

            # show the almanack score output
            print(almanack_score_output)  # noqa: T201

            # return non-zero exit code for failures
            sys.exit(2)

        # show the almanack score output
        print(almanack_score_output)  # noqa: T201

        # exit with zero (no failures)
        sys.exit(0)


def trigger():
    """
    Trigger the CLI to run.
    """
    fire.Fire(AlmanackCLI)


if __name__ == "__main__":
    """
    Setup the CLI with python-fire for the almanack package.

    This allows the function `check` to be ran through the
    command line interface.
    """

    trigger()
