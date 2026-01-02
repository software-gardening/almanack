"""
Setup almanack CLI through python-fire
"""

import importlib
import json
import shutil
import sys
from datetime import datetime, timezone
from typing import List, Optional

import fire
import pandas as pd
from tabulate import tabulate

from almanack.batch_processing import process_repositories_batch
from almanack.metrics.data import (
    _get_almanack_version,
    gather_failed_almanack_metric_checks,
    get_table,
    process_repo_for_almanack,
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
                ]
                for metric in failed_metrics
                if metric["name"] != "repo-almanack-score"
            ]

            # gather the max length of the ID and Name columns for use in formatting below
            max_id_length = max(len(metric[0]) for metric in failures_output_table)
            max_name_length = max(len(metric[1]) for metric in failures_output_table)

            # calculate the max width for the final column in output
            max_width = (shutil.get_terminal_size().columns) - (
                max_id_length + max_name_length + 12
            )

            # show a table of failures
            print(  # noqa: T201
                str(
                    tabulate(
                        tabular_data=failures_output_table,
                        headers=["ID", "Name", "Guidance"],
                        tablefmt="rounded_grid",
                        # set a dynamic width for each column in the table
                        # where the None is no max width and the final column
                        # is a dynamic max width of the terminal minus the other
                        # column lengths.
                        maxcolwidths=[
                            None,
                            None,
                            max_width if max_width > 0 else 30,
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

    def batch(  # noqa: PLR0913
        self,
        output_path: Optional[str] = None,
        parquet_path: Optional[str] = None,
        repo_urls: Optional[List[str]] = None,
        column: str = "github_link",
        batch_size: int = 500,
        max_workers: int = 16,
        limit: Optional[int] = None,
        compression: str = "zstd",
        show_repo_progress: bool = True,
        processor: Optional[str] = None,
        executor: str = "process",
        split_batches: bool = False,
        collect_dataframe: bool = True,
        show_batch_progress: bool = False,
        show_errors: bool = True,
    ) -> None:
        """
        Run Almanack across many repositories defined in a parquet file or a provided list.

        Example:
            almanack batch links.parquet results.parquet --column github_link --batch_size 1000 --max_workers 8

        Args:
            output_path: Optional destination parquet for aggregated results. If omitted, results are printed as JSON.
            parquet_path: Parquet file containing repository URLs.
            repo_urls: Optional list of repository URLs to process.
            output_path: Destination parquet for aggregated results.
            column: Column name holding repository URLs.
            batch_size: Repositories per batch.
            max_workers: Parallel workers per batch.
            limit: Optional maximum repositories to process.
            compression: Parquet compression codec (default zstd).
            show_repo_progress: Print per-repository progress to stdout.
            show_batch_progress: Print per-batch progress to stdout.
            show_errors: Print repository-level errors to stdout.
            processor: Optional import path to a processor function (e.g., module:function). Defaults to Almanack processor.
            executor: Parallelism backend: "process" (default) or "thread".
            split_batches: If True, write one parquet file per batch inside output_path (must be a directory).
            collect_dataframe: If False, skip retaining the combined DataFrame (avoids large in-memory data).
        """

        if repo_urls:
            if isinstance(repo_urls, str):
                repo_urls = [url.strip() for url in repo_urls.split(",") if url.strip()]
            repo_urls = [url for url in repo_urls if url]
        elif parquet_path:
            df_links = pd.read_parquet(parquet_path)
            if column not in df_links.columns:
                raise ValueError(
                    f"'{column}' column not found. Available columns: {list(df_links.columns)}"
                )
            repo_urls = df_links[column].dropna().drop_duplicates().tolist()
        else:
            raise ValueError("Provide either repo_urls or parquet_path.")

        if executor.lower() == "thread":
            from concurrent.futures import ThreadPoolExecutor  # noqa: PLC0415

            executor_cls = ThreadPoolExecutor
        else:
            from concurrent.futures import ProcessPoolExecutor  # noqa: PLC0415

            executor_cls = ProcessPoolExecutor

        processor_fn = process_repo_for_almanack
        if processor:
            try:
                module_path, func_name = processor.split(":")
            except ValueError as exc:
                raise ValueError(
                    "processor must be provided as 'module:function'"
                ) from exc
            module = importlib.import_module(module_path)
            processor_fn = getattr(module, func_name)

        df = process_repositories_batch(
            repo_urls=repo_urls,
            output_path=output_path,
            batch_size=batch_size,
            max_workers=max_workers,
            limit=limit,
            compression=compression,
            processor=processor_fn,
            executor_cls=executor_cls,
            show_repo_progress=show_repo_progress,
            split_batches=split_batches,
            collect_dataframe=collect_dataframe,
            show_batch_progress=show_batch_progress,
            show_errors=show_errors,
        )

        if output_path:
            count = len(df) if df is not None else "unknown"
            print(  # noqa: T201
                f"Wrote {count} records to {output_path} "
                f"(input {len(repo_urls)} repos, batch_size={batch_size}, max_workers={max_workers})"
            )
        elif df is not None:
            print(df.to_json(orient="records"))  # noqa: T201
        else:
            print("[]")  # noqa: T201


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
