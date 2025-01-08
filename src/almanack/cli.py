"""
Setup almanack CLI through python-fire
"""

import json
import shutil
import sys
from datetime import datetime, timezone

import fire
from tabulate import tabulate

from .metrics.data import gather_failed_almanack_metrics, get_table


class AlmanackCLI(object):
    """
    Almanack CLI class for Google Fire
    """

    def table(self, repo_path: str) -> str:
        """
        Used through CLI to
        generate a table of metrics

        This enables the use of CLI such as:
        `almanack table <repo path>`
        """

        # serialize the JSON as a string
        return json.dumps(
            # gather table data from Almanack
            get_table(repo_path=repo_path)
        )

    def check(self, repo_path: str) -> str:
        """
        Used through CLI to
        check table of metrics for
        boolean values with a non-zero
        sustainability direction
        for failures.

        This enables the use of CLI such as:
        `almanack check <repo path>`
        """

        # header for CLI output
        datetime_now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        print(f"Running Sofftware Gardening Almanack checks at {datetime_now}.")
        print(f"Target repository path: {repo_path}")

        # gather failed metrics
        failed_metrics = gather_failed_almanack_metrics(repo_path=repo_path)

        # gather almanack score metrics
        almanack_score_metrics = next(
            (
                metric["result"]
                for metric in failed_metrics
                if metric["name"] == "repo-almanack-score"
            ),
            None,
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

            print(
                f"Software Gardening Almanack score: {100 * almanack_score_metrics['almanack-score']:.2f}% "
                f"({almanack_score_metrics['almanack-score-numerator']}/"
                f"{almanack_score_metrics['almanack-score-denominator']})"
            )

            # return non-zero exit code for failures
            return sys.exit(1)

        print(
            f"Software Gardening Almanack score: {100 * almanack_score_metrics['almanack-score']:.2f}% "
            f"({almanack_score_metrics['almanack-score-numerator']}/"
            f"{almanack_score_metrics['almanack-score-denominator']})"
        )
        return sys.exit(0)


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
