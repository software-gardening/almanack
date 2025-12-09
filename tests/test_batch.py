"""
Tests for almanack.batch utilities.
"""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

from almanack.batch import (
    process_repositories_batch,
    sanitize_for_parquet,
)


def _sample_processor(repo_url: str) -> dict:
    """Top-level processor used for multiprocessing-safe tests."""
    if "fail" in repo_url:
        raise RuntimeError("boom")
    return {
        "Repository URL": repo_url,
        "checks_total": 1,
        "checks_passed": 1,
        "checks_pct": 100.0,
        "metadata": {"foo": "bar"},
        "tags": ["one", "two"],
    }


def test_sanitize_for_parquet_handles_nested_types():
    df = pd.DataFrame(
        {
            "dict_col": [{"a": 1, "b": "two"}, None],
            "list_col": [[1, 2], None],
            "object_col": [Path("/tmp/example"), None],
        }
    )

    sanitized = sanitize_for_parquet(df)

    assert set(sanitized.columns) == {
        "dict_col_a",
        "dict_col_b",
        "list_col",
        "object_col",
    }
    assert sanitized["list_col"].iloc[0] == "[1, 2]"
    assert sanitized["object_col"].iloc[0] == "/tmp/example"


def test_process_repositories_batch_writes_single_parquet(tmp_path):
    repo_urls = [
        "https://github.com/example/success",
        "https://github.com/example/fail",
    ]
    output_file = tmp_path / "results" / "almanack.parquet"

    df = process_repositories_batch(
        repo_urls,
        output_path=output_file,
        batch_size=1,
        max_workers=2,
        processor=_sample_processor,
        executor_cls=ThreadPoolExecutor,
        show_repo_progress=False,
        show_errors=False,
    )

    assert output_file.exists()
    assert len(df) == 2
    assert "Repository URL" in df.columns
    assert "metadata_foo" in df.columns
    assert "almanack_error" in df.columns
    assert (
        df.loc[
            df["Repository URL"] == "https://github.com/example/fail", "almanack_error"
        ]
        .notna()
        .all()
    )

    from_file = pd.read_parquet(output_file)
    assert len(from_file) == 2
    assert "metadata_foo" in from_file.columns
    assert from_file["checks_total"].dtype.kind in ("i", "f")
    # Error column should persist even when only one repo fails
    assert "almanack_error" in from_file.columns


def test_process_repositories_batch_split_batches(tmp_path):
    repo_urls = [
        "https://github.com/example/one",
        "https://github.com/example/two",
    ]
    output_dir = tmp_path / "results"

    df = process_repositories_batch(
        repo_urls,
        output_path=output_dir,
        split_batches=True,
        batch_size=1,
        max_workers=1,
        processor=_sample_processor,
        executor_cls=ThreadPoolExecutor,
        show_repo_progress=False,
        show_errors=False,
    )

    # Two repos, batch_size=1 => two files
    batch_files = sorted(output_dir.glob("batch_*.parquet"))
    assert len(batch_files) == 2

    assert len(df) == 2
    from_file = pd.read_parquet(batch_files[0])
    assert "Repository URL" in from_file.columns
    assert "almanack_error" in from_file.columns


def test_process_repositories_batch_without_output_path():
    repo_urls = ["https://github.com/example/success"]

    df = process_repositories_batch(
        repo_urls,
        output_path=None,
        collect_dataframe=True,
        batch_size=1,
        max_workers=1,
        processor=_sample_processor,
        executor_cls=ThreadPoolExecutor,
        show_repo_progress=False,
        show_errors=False,
    )

    assert not df.empty
    assert "Repository URL" in df.columns
    assert df["checks_total"].dtype.kind in ("i", "f")


def test_process_repositories_batch_without_collecting():
    repo_urls = ["https://github.com/example/success"]

    df = process_repositories_batch(
        repo_urls,
        output_path=None,
        collect_dataframe=False,
        batch_size=1,
        max_workers=1,
        processor=_sample_processor,
        executor_cls=ThreadPoolExecutor,
        show_repo_progress=False,
        show_errors=False,
    )

    assert df is None
