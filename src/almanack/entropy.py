import math

from git_parser import calculate_loc_changes


def calculate_entropy(repo_path, source_commit, target_commit, file_names):
    # Step 1: Get lines of code changed using calculate_loc_changes
    changes = calculate_loc_changes(repo_path, source_commit, target_commit, file_names)

    # Step 2: Calculate total lines changed
    total_changes = sum(changes.values())
    if total_changes == 0:
        return 0.0

    # Step 3: Calculate probabilities
    probabilities = {
        file_name: changes[file_name] / total_changes for file_name in changes
    }

    # Step 4: Calculate entropy
    entropy = -sum(
        probabilities[file_name] * math.log(probabilities[file_name], 2)
        for file_name in changes
    )
    print(entropy)
    return entropy
