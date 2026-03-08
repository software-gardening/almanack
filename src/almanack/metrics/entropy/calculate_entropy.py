"""Calculate software change entropy and decay-weighted history complexity."""

import math
import pathlib
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Union

import pygit2

from almanack.git import get_loc_changed


@dataclass(frozen=True)
class HistoryComplexityConfig:
    """Configuration values for the decay-weighted history complexity metric.

    Attributes:
        decay_factor: Time scale (in hours) for exponential down-weighting of
            older burst periods. Larger values make older periods lose influence
            more slowly; smaller values make them fade faster.
        quiet_time_seconds: Maximum allowed time gap between adjacent commit
            events in the same burst period. If the gap is larger than this
            threshold, a new burst period starts.
    """

    decay_factor: float = 10.0
    quiet_time_seconds: int = 3600


def calculate_normalized_entropy(
    repo_path: pathlib.Path,
    source_commit: pygit2.Commit,
    target_commit: pygit2.Commit,
    file_names: list[str],
) -> dict[str, float]:
    """Calculate per-file normalized Shannon entropy for changed lines.

    The function computes entropy using per-file change probabilities between
    `source_commit` and `target_commit`, where each probability is:
    `changed_lines_in_file / total_changed_lines_across_files`.

    Args:
        repo_path: Path to the local Git repository.
        source_commit: Commit that defines the start of the comparison range.
        target_commit: Commit that defines the end of the comparison range.
        file_names: Repository-relative file paths to include in the calculation.

    Returns:
        Mapping of file path to that file's entropy contribution.

    References:
        Hassan, A. E. (2009). Predicting faults using the complexity of code
        changes. 2009 IEEE 31st International Conference on Software
        Engineering, 78-88. https://doi.org/10.1109/ICSE.2009.5070510
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
    """Convert a commit input into a concrete `pygit2.Commit`.

    Args:
        repo: Open repository used to look up commit reference strings.
        commit_ref: Existing commit object or rev-parse compatible commit string.

    Returns:
        Commit object for `commit_ref`.
    """
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
    """Collect per-period tracked-file change totals separated by quiet windows (periods in a repository without commits).

    This function walks commits from `target_commit` backwards to
    `source_commit`, extracts tracked-file line changes from each commit, and
    then groups these "commit events" into burst periods. A new period starts when the
    elapsed time between consecutive commit events is greater than
    `quiet_time_seconds`.

    Args:
        repo: Open repository used to read commit history and diffs.
        source_commit: Commit that marks the start boundary (exclusive).
        target_commit: Commit that marks the end boundary (inclusive).
        tracked_files: File paths that should contribute to change totals.
        quiet_time_seconds: Threshold separating consecutive burst periods.

    Returns:
        Time-ordered list of periods. Each item contains the period end time
        (Unix timestamp) and file-level changed-line total counts for that period.
    """
    commit_events: list[tuple[int, dict[str, int]]] = []
    walker = repo.walk(target_commit.id, pygit2.GIT_SORT_TIME)

    for commit in walker:
        if commit.id == source_commit.id:
            break
        if not commit.parents:
            continue

        diff = repo.diff(commit.parents[0], commit)
        file_changes: dict[str, int] = defaultdict(int)
        for patch in diff:
            file_path = patch.delta.new_file.path or patch.delta.old_file.path
            if file_path not in tracked_files:
                continue

            changed_lines = sum(
                1
                for hunk in patch.hunks
                for line in hunk.lines
                if line.origin in {"+", "-"}
            )
            if changed_lines > 0:
                file_changes[file_path] += changed_lines

        if file_changes:
            commit_events.append((commit.commit_time, dict(file_changes)))

    if not commit_events:
        return []

    return _group_commit_events_by_quiet_window(
        commit_events=commit_events,
        quiet_time_seconds=quiet_time_seconds,
    )


def _group_commit_events_by_quiet_window(
    commit_events: list[tuple[int, dict[str, int]]],
    quiet_time_seconds: int,
) -> list[tuple[int, dict[str, int]]]:
    """Group commit events into burst periods separated by quiet windows.

    Args:
        commit_events: Sequence of `(event_time, file_changes)` tuples.
        quiet_time_seconds: Threshold that starts a new period when exceeded.

    Returns:
        Time-ordered periods with end timestamp and aggregated file changes.
    """
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
    """Calculate decay-weighted history complexity for each tracked file.

    For each burst period, this computes Shannon entropy across file-level
    changed-line probabilities, then applies exponential decay by period age.

    Args:
        repo_path: Path to the local Git repository.
        source_commit: Commit object or reference string for range start.
        target_commit: Commit object or reference string for range end.
        file_names: Repository-relative file paths to score.
        config: Decay and period-grouping configuration.

    Returns:
        Mapping of file path to decay-weighted history complexity score.

    Raises:
        ValueError: If `config.decay_factor` is less than or equal to zero.

    References:
        Hassan, A. E. (2009). Predicting faults using the complexity of code
        changes. 2009 IEEE 31st International Conference on Software
        Engineering, 78-88. https://doi.org/10.1109/ICSE.2009.5070510
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
    """Calculate the mean decay-weighted history complexity across files.

    Args:
        repo_path: Path to the local Git repository.
        source_commit: Commit object or reference string for range start.
        target_commit: Commit object or reference string for range end.
        file_names: Repository-relative file paths to include in the mean.
        config: Decay and period-grouping configuration.

    Returns:
        Mean file-level history complexity score, or `0.0` for no files.

    References:
        Hassan, A. E. (2009). Predicting faults using the complexity of code
        changes. 2009 IEEE 31st International Conference on Software
        Engineering, 78-88. https://doi.org/10.1109/ICSE.2009.5070510
    """
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
    """Calculate mean normalized entropy across the provided files.

    Args:
        repo_path: Path to the local Git repository.
        source_commit: Commit that defines the start of the comparison range.
        target_commit: Commit that defines the end of the comparison range.
        file_names: Repository-relative file paths to include in the calculation.

    Returns:
        Mean of per-file normalized entropy values, or `0.0` for no files.

    References:
        Hassan, A. E. (2009). Predicting faults using the complexity of code
        changes. 2009 IEEE 31st International Conference on Software
        Engineering, 78-88. https://doi.org/10.1109/ICSE.2009.5070510
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
