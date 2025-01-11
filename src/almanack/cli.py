"""
Setup almanack CLI through python-fire
"""

import json
import shutil
import sys
from datetime import datetime, timezone

import fire
from tabulate import tabulate

from .metrics.data import (
    _get_almanack_version,
    gather_failed_almanack_metric_checks,
    get_table,
)


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

    def table(self, repo_path: str) -> None:
        """
        Used through CLI to
        generate a table of metrics

        This enables the use of CLI such as:
        `almanack table <repo path>`

        Args:
            repo_path (str):
                The path to the repository to analyze.
        """

        # print serialized JSON as a string
        print(
            json.dumps(
                # gather table data from Almanack
                get_table(repo_path=repo_path)
            )
        )

        # exit with zero status for no errors
        # (we don't check for failures with this
        # CLI option.)
        sys.exit(0)

    def check(self, repo_path: str) -> None:
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
        """

        # header for CLI output
        datetime_now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        print(
            "Running Software Gardening Almanack checks.",
            f"Datetime: {datetime_now}",
            f"Almanack version: {_get_almanack_version()}",
            f"Target repository path: {repo_path}",
            sep="\n",
        )

        # gather failed metrics
        failed_metrics = gather_failed_almanack_metric_checks(repo_path=repo_path)

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
            f"Software Gardening Almanack score: {100 * almanack_score_metrics['almanack-score']:.2f}% "
            f"({almanack_score_metrics['almanack-score-numerator']}/"
            f"{almanack_score_metrics['almanack-score-denominator']})"
        )

        # if we have under 1 almanack score, we have failures
        # and show the guidance for those failures with a
        # non-zero exit.
        if almanack_score_metrics["almanack-score"] != 1:

            # introduce a table of output in CLI
            print("The following Software Gardening Almanack metrics have failed:")

            # Format the output
            failures_output_table = [
                [metric["id"], metric["name"], metric["correction_guidance"]]
                for metric in failed_metrics
                if metric["name"] != "repo-almanack-score"
            ]

            # gather the max length of the ID and Name columns for use in formatting below
            max_id_length = max(len(metric[0]) for metric in failures_output_table)
            max_name_length = max(len(metric[1]) for metric in failures_output_table)

            # show a table of failures
            print(
                str(
                    tabulate(
                        failures_output_table,
                        ["ID", "Name", "Guidance"],
                        tablefmt="rounded_grid",
                        # set a dynamic width for each column in the table
                        # where the None is no max width and the final column
                        # is a dynamic max width of the terminal minus the other
                        # column lengths.
                        maxcolwidths=[
                            None,
                            None,
                            (shutil.get_terminal_size().columns)
                            - (max_id_length + max_name_length + 12),
                        ],
                    )
                )
            )

            # show the almanack score output
            print(almanack_score_output)

            # return non-zero exit code for failures
            sys.exit(1)

        # show the almanack score output
        print(almanack_score_output)

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
