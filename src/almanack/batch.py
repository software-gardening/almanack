"""
Batch processing utilities for running Almanack across many repositories.
"""

import json
from concurrent.futures import Executor, ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable, List, Optional, Sequence, Type, Union

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from almanack.metrics.data import process_repo_for_almanack

RepositoryProcessor = Callable[[str], dict[str, Any]]


def sanitize_for_parquet(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans a DataFrame so all columns are parquet-safe.

    - Expands dict columns into multiple fields.
    - Converts lists into JSON strings.
    - Casts generic object types into strings.

    Args:
        df: Input DataFrame with raw metrics.

    Returns:
        df: Sanitized DataFrame safe for parquet storage.
    """
    for col in df.columns:
        # Check if column contains dicts
        if df[col].apply(lambda x: isinstance(x, dict)).any():
            nested = pd.json_normalize(df[col])
            nested.columns = [f"{col}_{c}" for c in nested.columns]
            df = df.drop(columns=[col]).join(nested)
        # Check if column contains lists
        elif df[col].apply(lambda x: isinstance(x, list)).any():
            df[col] = df[col].apply(
                lambda x: json.dumps(x) if isinstance(x, list) else x
            )
        # Fallback for generic objects
        elif df[col].dtype == "object":
            df[col] = df[col].astype(str)
    return df

def process_repositories_batch(
    repo_urls: Sequence[str],
    *,
    output_path: Union[str, Path],
    batch_size: int = 500,
    max_workers: int = 16,
    limit: Optional[int] = None,
    compression: str = "zstd",
    processor: RepositoryProcessor = process_repo_for_almanack,
    executor_cls: Type[Executor] = ProcessPoolExecutor,
    show_progress: bool = True,
) -> pd.DataFrame:
    """
    Processes repositories in batches and writes results to a single parquet file.

    Args:
        repo_urls: Iterable of repository URLs to process.
        output_path: Destination parquet path for all results.
        batch_size: Number of repositories per batch.
        max_workers: Maximum parallel workers for each batch.
        limit: Optional maximum number of repositories to process.
        compression: Parquet compression codec (default: zstd).
        processor: Callable used to process a repository (default: process_repo_for_almanack).
        executor_cls: Executor class used for parallelism (default: ProcessPoolExecutor).
        show_progress: Whether to print progress to stdout.

    Returns:
        A DataFrame containing all processed results.
    """
    filtered_urls = [url for url in repo_urls if url]
    repo_list: List[str] = list(
        dict.fromkeys(filtered_urls)
    )  # de-duplicate while preserving order
    if limit is not None:
        repo_list = repo_list[:limit]

    total_repos = len(repo_list)
    if total_repos == 0:
        return pd.DataFrame()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    batches: List[pd.DataFrame] = []
    repo_count = 0
    writer: Optional[pq.ParquetWriter] = None

    try:
        for start in range(0, total_repos, batch_size):
            end = min(start + batch_size, total_repos)
            batch_urls = repo_list[start:end]

            with executor_cls(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(processor, repo_url): repo_url
                    for repo_url in batch_urls
                }

                batch_results = []

                for future in as_completed(futures):
                    repo_count += 1
                    repo_url = futures[future]
                    try:
                        result_dict = future.result()
                    except Exception as exc:
                        result_dict = {
                            "Repository URL": repo_url,
                            "almanack_error": str(exc),
                            "checks_total": None,
                            "checks_passed": None,
                            "checks_pct": None,
                        }
                    if show_progress:
                        print(f"[{repo_count}/{total_repos}]")  # noqa: T201
                    batch_results.append(result_dict)

            df_batch = sanitize_for_parquet(pd.DataFrame(batch_results))
            batches.append(df_batch)

            if not df_batch.empty:
                table = pa.Table.from_pandas(df_batch, preserve_index=False)
                if writer is None:
                    writer = pq.ParquetWriter(
                        where=output_path,
                        schema=table.schema,
                        compression=compression,
                    )
                writer.write_table(table)
    finally:
        if writer is not None:
            writer.close()

    if not batches:
        return pd.DataFrame()

    return pd.concat(batches, ignore_index=True)
