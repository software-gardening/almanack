"""
Tests for almanack.batch utilities.
"""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

from almanack.batch import (
    load_repo_urls_from_parquet,
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
        show_progress=False,
    )

    assert output_file.exists()
    assert len(df) == 2
    assert "Repository URL" in df.columns
    assert "metadata_foo" in df.columns
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


def test_load_repo_urls_from_parquet(tmp_path):
    parquet_path = tmp_path / "links.parquet"
    pd.DataFrame({"github_link": ["a", "b", "a"], "other": [1, 2, 3]}).to_parquet(
        parquet_path
    )

    loaded = load_repo_urls_from_parquet(parquet_path, column="github_link", limit=2)

    assert loaded == ["a", "b"]
