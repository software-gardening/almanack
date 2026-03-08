"""
Testing entropy functionality
"""

import pathlib
from datetime import datetime, timedelta

import pygit2
import pytest

from almanack.metrics.entropy.calculate_entropy import (
    HistoryComplexityConfig,
    calculate_aggregate_entropy,
    calculate_aggregate_history_complexity_with_decay,
    calculate_history_complexity_with_decay,
    calculate_normalized_entropy,
)
from tests.data.almanack.repo_setup.create_repo import repo_setup
from tests.test_git import get_most_recent_commits


def test_calculate_normalized_entropy(
    entropy_repository_paths: dict[str, pathlib.Path],
    repo_file_sets: dict[str, list[str]],
) -> None:
    """
    Test the calculate_normalized_entropy function.
    """
    for label, repo_path in entropy_repository_paths.items():
        # Extract two most recent commits: source and target
        source_commit, target_commit = get_most_recent_commits(repo_path)

        # Call calculate_normalized_entropy function
        entropies = calculate_normalized_entropy(
            repo_path, source_commit, target_commit, repo_file_sets[label]
        )

        assert entropies  # Check if the entropies dictionary is not empty

        for entropy in entropies.values():
            assert (
                0 <= entropy <= 1
            )  # Check if entropy is non-negative and within normalized range of [0,1]


def test_calculate_aggregate_entropy(
    entropy_repository_paths: dict[str, pathlib.Path],
    repo_file_sets: dict[str, list[str]],
) -> None:
    """
    Test that calculate_aggregate_entropy function
    """
    repo_entropies = {}

    for label, repo_path in entropy_repository_paths.items():
        # Extract two most recent commits: source and target
        source_commit, target_commit = get_most_recent_commits(repo_path)
        # Call calculate_normalized_entropy function
        normalized_entropy = calculate_aggregate_entropy(
            repo_path, source_commit, target_commit, repo_file_sets[label]
        )
        repo_entropies[label] = normalized_entropy

    # Ensure that repositories with different entropy levels have different aggregated scores
    assert repo_entropies["3_file_repo"] > repo_entropies["1_file_repo"]


def test_calculate_history_complexity_with_decay(tmp_path: pathlib.Path) -> None:
    """
    Test HCM_1d behavior with one-hour burst periods and exponential decay.
    """
    base_time = datetime(2025, 1, 1, 10, 0, 0)
    repo_path = tmp_path / "hcm_decay_repo"
    file_names = ["file_a.md", "file_b.md", "file_c.md"]

    repo_setup(
        repo_path=repo_path,
        files=[
            {
                "files": {
                    "file_a.md": "base\n",
                    "file_b.md": "base\n",
                    "file_c.md": "base\n",
                },
                "commit-date": base_time,
            },
            {
                "files": {
                    "file_a.md": "base\nold_a_1\n",
                    "file_b.md": "base\nold_b_1\n",
                    "file_c.md": "base\n",
                },
                "commit-date": base_time + timedelta(minutes=10),
            },
            {
                "files": {
                    "file_a.md": "base\nold_a_1\nold_a_2\n",
                    "file_b.md": "base\nold_b_1\nold_b_2\n",
                    "file_c.md": "base\n",
                },
                "commit-date": base_time + timedelta(minutes=20),
            },
            {
                "files": {
                    "file_a.md": "base\nold_a_1\nold_a_2\n",
                    "file_b.md": "base\nold_b_1\nold_b_2\nnew_b_1\n",
                    "file_c.md": "base\nnew_c_1\n",
                },
                "commit-date": base_time + timedelta(hours=3),
            },
        ],
    )
    repo = pygit2.Repository(str(repo_path))
    commits = list(repo.walk(repo.head.target, pygit2.GIT_SORT_TIME))
    source_commit = str(commits[-1].id)
    target_commit = str(commits[0].id)

    hcm_decay = calculate_history_complexity_with_decay(
        repo_path=repo_path,
        source_commit=source_commit,
        target_commit=target_commit,
        file_names=file_names,
    )

    assert set(hcm_decay.keys()) == set(file_names)
    assert all(score >= 0 for score in hcm_decay.values())
    assert hcm_decay["file_b.md"] > hcm_decay["file_a.md"]
    assert hcm_decay["file_b.md"] > hcm_decay["file_c.md"]

    aggregate_hcm_decay = calculate_aggregate_history_complexity_with_decay(
        repo_path=repo_path,
        source_commit=source_commit,
        target_commit=target_commit,
        file_names=file_names,
    )
    expected_aggregate = sum(hcm_decay.values()) / len(file_names)
    assert aggregate_hcm_decay == pytest.approx(expected_aggregate)


def test_calculate_history_complexity_with_decay_decay_factor(
    tmp_path: pathlib.Path,
) -> None:
    """
    Test that a smaller decay factor decreases the effect of older periods.
    """
    base_time = datetime(2025, 1, 1, 10, 0, 0)
    repo_path = tmp_path / "hcm_decay_factor_repo"
    file_names = ["file_a.md", "file_b.md", "file_c.md"]

    repo_setup(
        repo_path=repo_path,
        files=[
            {
                "files": {
                    "file_a.md": "base\n",
                    "file_b.md": "base\n",
                    "file_c.md": "base\n",
                },
                "commit-date": base_time,
            },
            {
                "files": {
                    "file_a.md": "base\nold_a_1\n",
                    "file_b.md": "base\nold_b_1\n",
                    "file_c.md": "base\n",
                },
                "commit-date": base_time + timedelta(minutes=10),
            },
            {
                "files": {
                    "file_a.md": "base\nold_a_1\nold_a_2\n",
                    "file_b.md": "base\nold_b_1\nold_b_2\n",
                    "file_c.md": "base\n",
                },
                "commit-date": base_time + timedelta(minutes=20),
            },
            {
                "files": {
                    "file_a.md": "base\nold_a_1\nold_a_2\n",
                    "file_b.md": "base\nold_b_1\nold_b_2\nnew_b_1\n",
                    "file_c.md": "base\nnew_c_1\n",
                },
                "commit-date": base_time + timedelta(hours=3),
            },
        ],
    )
    repo = pygit2.Repository(str(repo_path))
    commits = list(repo.walk(repo.head.target, pygit2.GIT_SORT_TIME))
    source_commit = str(commits[-1].id)
    target_commit = str(commits[0].id)

    high_decay = calculate_history_complexity_with_decay(
        repo_path=repo_path,
        source_commit=source_commit,
        target_commit=target_commit,
        file_names=file_names,
        config=HistoryComplexityConfig(decay_factor=100.0),
    )
    low_decay = calculate_history_complexity_with_decay(
        repo_path=repo_path,
        source_commit=source_commit,
        target_commit=target_commit,
        file_names=file_names,
        config=HistoryComplexityConfig(decay_factor=1.0),
    )

    # file_a.md only appears in the older period, so stronger decay lowers its score.
    assert low_decay["file_a.md"] < high_decay["file_a.md"]


def test_calculate_history_complexity_with_decay_single_period(
    tmp_path: pathlib.Path,
) -> None:
    """
    Test that a large quiet window collapses changes into one burst period.
    """
    base_time = datetime(2025, 1, 1, 10, 0, 0)
    repo_path = tmp_path / "hcm_single_period_repo"
    file_names = ["file_a.md", "file_b.md", "file_c.md"]

    repo_setup(
        repo_path=repo_path,
        files=[
            {
                "files": {
                    "file_a.md": "base\n",
                    "file_b.md": "base\n",
                    "file_c.md": "base\n",
                },
                "commit-date": base_time,
            },
            {
                "files": {
                    "file_a.md": "base\na_1\n",
                    "file_b.md": "base\nb_1\n",
                    "file_c.md": "base\n",
                },
                "commit-date": base_time + timedelta(minutes=10),
            },
            {
                "files": {
                    "file_a.md": "base\na_1\n",
                    "file_b.md": "base\nb_1\n",
                    "file_c.md": "base\nc_1\n",
                },
                "commit-date": base_time + timedelta(hours=3),
            },
        ],
    )
    repo = pygit2.Repository(str(repo_path))
    commits = list(repo.walk(repo.head.target, pygit2.GIT_SORT_TIME))
    source_commit = str(commits[-1].id)
    target_commit = str(commits[0].id)

    hcm_single_period = calculate_history_complexity_with_decay(
        repo_path=repo_path,
        source_commit=source_commit,
        target_commit=target_commit,
        file_names=file_names,
        config=HistoryComplexityConfig(quiet_time_seconds=24 * 3600),
    )

    assert hcm_single_period["file_a.md"] == pytest.approx(
        hcm_single_period["file_b.md"]
    )
    assert hcm_single_period["file_b.md"] == pytest.approx(
        hcm_single_period["file_c.md"]
    )
