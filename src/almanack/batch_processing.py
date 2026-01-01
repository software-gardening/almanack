"""
Batch processing utilities for running Almanack across many repositories.
"""

import json
import logging
from concurrent.futures import Executor, ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable, List, Optional, Sequence, Type, Union

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from almanack.metrics.data import process_repo_for_almanack

RepositoryProcessor = Callable[[str], dict[str, Any]]
LOGGER = logging.getLogger(__name__)


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
        series = df[col]
        # Check if column contains dicts
        if series.apply(lambda x: isinstance(x, dict)).any():
            nested = pd.json_normalize(series)
            nested.columns = [f"{col}_{c}" for c in nested.columns]
            df = df.drop(columns=[col]).join(nested)
        # Check if column contains lists
        elif series.apply(lambda x: isinstance(x, list)).any():
            df[col] = series.apply(
                lambda x: json.dumps(x) if isinstance(x, list) else x
            )
        # Fallback for generic objects
        elif series.dtype == "object":
            non_null = series.dropna()
            is_numeric_like = (
                not non_null.empty
                and non_null.map(
                    lambda x: isinstance(x, (int, float, bool, np.number))
                ).all()
            )
            if is_numeric_like:
                df[col] = pd.to_numeric(series, errors="coerce")
            else:
                # Preserve None as None; stringify only real values
                df[col] = series.apply(lambda x: x if x is None else str(x))
    return df


def _nullable_dtype(dtype: Any) -> Any:
    """Map to nullable pandas dtypes so missing values keep schema."""
    if pd.api.types.is_integer_dtype(dtype):
        return "Int64"
    if pd.api.types.is_bool_dtype(dtype):
        return "boolean"
    if pd.api.types.is_object_dtype(dtype):
        return "string"
    return dtype


def process_repositories_batch(  # noqa: C901, PLR0913, PLR0912, PLR0915
    repo_urls: Sequence[str],
    output_path: Optional[Union[str, Path]] = None,
    split_batches: bool = False,
    collect_dataframe: bool = True,
    batch_size: int = 500,
    max_workers: int = 16,
    limit: Optional[int] = None,
    compression: str = "zstd",
    processor: RepositoryProcessor = process_repo_for_almanack,
    executor_cls: Type[Executor] = ProcessPoolExecutor,
    show_repo_progress: bool = True,
    show_batch_progress: bool = False,
    show_errors: bool = True,
) -> Optional[pd.DataFrame]:
    """
    Processes repositories in batches and writes results to a single parquet file.

    Args:
        repo_urls: Iterable of repository URLs to process.
        output_path: Optional destination parquet path for all results.
        split_batches: If True, write one parquet file per batch to the directory at output_path.
                       If False (default), append all batches into a single parquet file.
        collect_dataframe: If False, skip retaining per-batch DataFrames and return None to reduce memory.
        batch_size: Number of repositories per batch.
        max_workers: Maximum parallel workers for each batch.
        limit: Optional maximum number of repositories to process.
        compression: Parquet compression codec (default: zstd).
        processor: Callable used to process a repository (default: process_repo_for_almanack).
        executor_cls: Executor class used for parallelism (default: ProcessPoolExecutor).
        show_repo_progress: Whether to print per-repository progress to stdout.
        show_batch_progress: Whether to print per-batch progress to stdout.
        show_errors: Whether to print repository-level errors to stdout.

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

    writer: Optional[pq.ParquetWriter] = None
    if output_path is not None:
        output_path = Path(output_path)
        if split_batches:
            output_path.mkdir(parents=True, exist_ok=True)
        else:
            output_path.parent.mkdir(parents=True, exist_ok=True)

    batches: List[pd.DataFrame] = []
    repo_count = 0
    batch_number = 0
    # Track the initial schema so later batches conform to it
    schema_columns: Optional[List[str]] = None
    schema_dtypes: dict[str, Any] = {}
    try:
        for start in range(0, total_repos, batch_size):
            batch_number += 1
            end = min(start + batch_size, total_repos)
            batch_urls = repo_list[start:end]

            if show_batch_progress:
                print(  # noqa: T201
                    f"[batch {batch_number}] processing {len(batch_urls)} repos "
                    f"({start + 1}-{end}/{total_repos})"
                )

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
                        if show_errors:
                            print(f"[error] {repo_url}: {exc}")  # noqa: T201
                    # Normalize presence of error field for schema stability
                    result_dict.setdefault("almanack_error", None)
                    if show_repo_progress:
                        print(f"[{repo_count}/{total_repos}]")  # noqa: T201
                    batch_results.append(result_dict)

            df_batch = sanitize_for_parquet(pd.DataFrame(batch_results))
            if df_batch.empty:
                continue

            if schema_columns is None:
                # Lock schema on first non-empty batch
                schema_columns = list(df_batch.columns)
                schema_dtypes = {
                    col: _nullable_dtype(df_batch[col].dtype) for col in schema_columns
                }
                df_batch = df_batch.astype(schema_dtypes)
            else:
                extra_cols = [c for c in df_batch.columns if c not in schema_columns]
                if extra_cols:
                    df_batch = df_batch.drop(columns=extra_cols)
                for col in schema_columns:
                    if col not in df_batch.columns:
                        # Add missing columns with the expected dtype
                        df_batch[col] = pd.Series(
                            [pd.NA] * len(df_batch), dtype=schema_dtypes[col]
                        )
                df_batch = df_batch[schema_columns]
                for col, dtype in schema_dtypes.items():
                    try:
                        df_batch[col] = df_batch[col].astype(dtype)
                    except Exception as exc:
                        # Avoid hard failures on cast; log and continue
                        LOGGER.debug("Skipping cast for column %s: %s", col, exc)
            if collect_dataframe:
                batches.append(df_batch)

            if output_path is not None and not df_batch.empty:
                if split_batches:
                    batch_file = output_path / f"batch_{batch_number}.parquet"
                    df_batch.to_parquet(
                        batch_file, compression=compression, index=False
                    )
                else:
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

    if not collect_dataframe:
        return None

    if not batches:
        return pd.DataFrame()

    return pd.concat(batches, ignore_index=True)
