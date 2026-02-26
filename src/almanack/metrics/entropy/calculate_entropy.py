"""
This module calculates the amount of Software information entropy
"""

import math
import pathlib
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Union

import pygit2

from almanack.git import get_loc_changed


@dataclass(frozen=True)
class HistoryComplexityConfig:
    """Configuration for history complexity metric with decay."""

    decay_factor: float = 10.0
    quiet_time_seconds: int = 3600


def calculate_normalized_entropy(
    repo_path: pathlib.Path,
    source_commit: pygit2.Commit,
    target_commit: pygit2.Commit,
    file_names: list[str],
) -> dict[str, float]:
    """
    Calculates the entropy of changes in specified files between two commits,
    inspired by Shannon's information theory entropy formula.
    Normalized relative to the total lines of code changes across specified files.
    We follow an approach described by Hassan (2009) (see references).

    Application of Entropy Calculation:
    Entropy measures the uncertainty in a given system. Calculating the entropy
    of lines of code (LoC) changed reveals the variability and complexity of
    modifications in each file. Higher entropy values indicate more unpredictable
    changes, helping identify potentially unstable code areas.

    Args:
        repo_path (str): The file path to the git repository.
        source_commit (pygit2.Commit): The git hash of the source commit.
        target_commit (pygit2.Commit): The git hash of the target commit.
        file_names (list[str]): List of file names to calculate entropy for.

    Returns:
        dict[str, float]: A dictionary mapping file names to their calculated entropy.

    References:
        * Hassan, A. E. (2009). Predicting faults using the complexity of code changes.
            2009 IEEE 31st International Conference on Software Engineering, 78-88.
            https://doi.org/10.1109/ICSE.2009.5070510
    """
    loc_changes = get_loc_changed(repo_path, source_commit, target_commit, file_names)
    # Calculate total lines of code changes across all specified files
    total_changes = sum(loc_changes.values())

    # Calculate the entropy for each file, relative to total changes
    entropy_calculation = {
        file_name: (
            -(
                (loc_changes[file_name] / total_changes)
                * math.log2(
                    loc_changes[file_name] / total_changes
                )  # Entropy Calculation
            )
            if loc_changes[file_name] != 0
            and total_changes
            != 0  # Avoid division by zero and ensure valid entropy calculation
            else 0.0
        )
        for file_name in loc_changes  # Iterate over each file in loc_changes dictionary
    }
    return entropy_calculation


def _resolve_commit(
    repo: pygit2.Repository, commit_ref: Union[str, pygit2.Commit]
) -> pygit2.Commit:
    """Resolve commit input into a pygit2 commit object."""
    if isinstance(commit_ref, pygit2.Commit):
        return commit_ref
    return repo.revparse_single(commit_ref)


def _collect_period_file_changes(
    repo: pygit2.Repository,
    source_commit: pygit2.Commit,
    target_commit: pygit2.Commit,
    tracked_files: set[str],
    quiet_time_seconds: int = 3600,
) -> list[tuple[int, dict[str, int]]]:
    """
    Collect file-level line change totals for one-hour burst periods.

    A new period starts when the elapsed time between consecutive commit events
    exceeds ``quiet_time_seconds``.
    """
    commit_events = _collect_commit_events(
        repo=repo,
        source_commit=source_commit,
        target_commit=target_commit,
        tracked_files=tracked_files,
    )

    if not commit_events:
        return []

    return _group_commit_events_by_quiet_window(
        commit_events=commit_events,
        quiet_time_seconds=quiet_time_seconds,
    )


def _collect_commit_events(
    repo: pygit2.Repository,
    source_commit: pygit2.Commit,
    target_commit: pygit2.Commit,
    tracked_files: set[str],
) -> list[tuple[int, dict[str, int]]]:
    """Collect changed line counts per file for each commit event."""
    commit_events: list[tuple[int, dict[str, int]]] = []
    walker = repo.walk(target_commit.id, pygit2.GIT_SORT_TIME)

    for commit in walker:
        if commit.id == source_commit.id:
            break
        changed_lines = _extract_tracked_file_changes(
            repo=repo,
            commit=commit,
            tracked_files=tracked_files,
        )
        if changed_lines:
            commit_events.append((commit.commit_time, changed_lines))
    return commit_events


def _extract_tracked_file_changes(
    repo: pygit2.Repository,
    commit: pygit2.Commit,
    tracked_files: set[str],
) -> dict[str, int]:
    """Extract line changes for tracked files from a single commit."""
    if not commit.parents:
        return {}

    diff = repo.diff(commit.parents[0], commit)
    changed_lines: dict[str, int] = defaultdict(int)

    for patch in diff:
        file_path = patch.delta.new_file.path or patch.delta.old_file.path
        if file_path not in tracked_files:
            continue
        changed_lines[file_path] += _count_patch_line_changes(patch)

    return dict(changed_lines)


def _count_patch_line_changes(patch: pygit2.Patch) -> int:
    """Count line additions and deletions for a patch."""
    additions = 0
    deletions = 0
    for hunk in patch.hunks:
        for line in hunk.lines:
            if line.origin == "+":
                additions += 1
            elif line.origin == "-":
                deletions += 1
    return additions + deletions


def _group_commit_events_by_quiet_window(
    commit_events: list[tuple[int, dict[str, int]]],
    quiet_time_seconds: int,
) -> list[tuple[int, dict[str, int]]]:
    """Group commit events into burst periods separated by quiet windows."""
    commit_events.sort(key=lambda event: event[0])
    periods: list[tuple[int, dict[str, int]]] = []
    current_end_time = commit_events[0][0]
    current_changes: dict[str, int] = defaultdict(int, commit_events[0][1])

    for event_time, event_changes in commit_events[1:]:
        if event_time - current_end_time > quiet_time_seconds:
            periods.append((current_end_time, dict(current_changes)))
            current_changes = defaultdict(int, event_changes)
        else:
            for file_name, changed in event_changes.items():
                current_changes[file_name] += changed
        current_end_time = event_time

    periods.append((current_end_time, dict(current_changes)))
    return periods


def calculate_history_complexity_with_decay(
    repo_path: pathlib.Path,
    source_commit: Union[str, pygit2.Commit],
    target_commit: Union[str, pygit2.Commit],
    file_names: list[str],
    config: HistoryComplexityConfig = HistoryComplexityConfig(),
) -> dict[str, float]:
    """
    Calculate history complexity metric with decay (HCM_1d) for each file.

    Periods are formed using a one-hour quiet threshold between commit events,
    as recommended by Hassan (2009). For each period we compute Shannon entropy
    over changed-line probabilities across files, then assign that period's
    entropy to changed files and apply an exponential time decay.
    """
    if config.decay_factor <= 0:
        raise ValueError("decay_factor must be greater than zero.")

    repo = pygit2.Repository(str(repo_path))
    source = _resolve_commit(repo, source_commit)
    target = _resolve_commit(repo, target_commit)

    period_changes = _collect_period_file_changes(
        repo=repo,
        source_commit=source,
        target_commit=target,
        tracked_files=set(file_names),
        quiet_time_seconds=config.quiet_time_seconds,
    )

    history_complexity = {file_name: 0.0 for file_name in file_names}
    if not period_changes:
        return history_complexity

    current_time = max(period_end for period_end, _ in period_changes)
    seconds_per_hour = 3600.0

    for period_end_time, file_changes in period_changes:
        total_changes = sum(file_changes.values())
        if total_changes <= 0:
            continue

        period_entropy = -sum(
            (changed / total_changes) * math.log2(changed / total_changes)
            for changed in file_changes.values()
            if changed > 0
        )
        age_in_hours = (current_time - period_end_time) / seconds_per_hour
        decay_weight = math.exp(-(age_in_hours / config.decay_factor))

        for file_name in file_changes:
            if file_name in history_complexity and file_changes[file_name] > 0:
                history_complexity[file_name] += decay_weight * period_entropy

    return history_complexity


def calculate_aggregate_history_complexity_with_decay(
    repo_path: pathlib.Path,
    source_commit: Union[str, pygit2.Commit],
    target_commit: Union[str, pygit2.Commit],
    file_names: List[str],
    config: HistoryComplexityConfig = HistoryComplexityConfig(),
) -> float:
    """Calculate the aggregate HCM_1d score as the mean file-level score."""
    history_complexity = calculate_history_complexity_with_decay(
        repo_path=repo_path,
        source_commit=source_commit,
        target_commit=target_commit,
        file_names=file_names,
        config=config,
    )
    num_files = len(file_names)
    return sum(history_complexity.values()) / num_files if num_files > 0 else 0.0


def calculate_aggregate_entropy(
    repo_path: pathlib.Path,
    source_commit: pygit2.Commit,
    target_commit: pygit2.Commit,
    file_names: List[str],
) -> float:
    """
    Computes the aggregated normalized entropy score from the output of
    calculate_normalized_entropy for specified a Git repository.
    Inspired by Shannon's information theory entropy formula.
    We follow an approach described by Hassan (2009) (see references).

    Args:
        repo_path (str): The file path to the git repository.
        source_commit (pygit2.Commit): The git hash of the source commit.
        target_commit (pygit2.Commit): The git hash of the target commit.
        file_names (list[str]): List of file names to calculate entropy for.

    Returns:
        float: Normalized entropy calculation.

    References:
        * Hassan, A. E. (2009). Predicting faults using the complexity of code changes.
            2009 IEEE 31st International Conference on Software Engineering, 78-88.
            https://doi.org/10.1109/ICSE.2009.5070510
    """
    # Get the entropy for each file
    entropy_calculation = calculate_normalized_entropy(
        repo_path, source_commit, target_commit, file_names
    )

    # Calculate total entropy of the repository
    total_entropy = sum(entropy_calculation.values())

    # Normalize total entropy by the number of files edited between the two commits
    num_files = len(file_names)
    normalized_total_entropy = (
        total_entropy / num_files if num_files > 0 else 0.0
    )  # Avoid division by zero (e.g., num_files = 0) and ensure valid entropy calculation
    return normalized_total_entropy
