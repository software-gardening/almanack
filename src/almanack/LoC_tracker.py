import git

def calculate_loc_changes(repo_path):
    """
    Calculate the absolute value of lines of code (LoC) changed (added or removed)
    in the given Git repository.

    :param repo_path: Path to the Git repository.
    :return: Total number of lines added and removed.
    """
    # repo = git.Repo(repo_path)

    # total_lines_changed = 0

    # for commit in repo.iter_commits():
    #     diff_stat = commit.stats.total
    #     lines_added = diff_stat['insertions']
    #     lines_removed = diff_stat['deletions']
    #     total_lines_changed += (lines_added + lines_removed)

    # return total_lines_changed
    repo = git.Repo(repo_path)
    total_lines_changed = 0

    for commit in repo.iter_commits():
        diff_stat = commit.stats.total
        lines_added = diff_stat['insertions']
        lines_removed = diff_stat['deletions']
        
        # Print debug information for each commit
        print(f"Commit: {commit.hexsha}")
        print(f"Lines added: {lines_added}, Lines removed: {lines_removed}")

        total_lines_changed += (lines_added + lines_removed)

    print(f"Total lines of code changed: {total_lines_changed}")
    return total_lines_changed

# Currently tracks the total amount of lines changed from first commit to the last one 