from git_parser import calculate_loc_changes
import math
from pathlib import Path

def entropy_calculation(repo_path: Path, source: str, target: str) -> dict[str, float]:
    loc_changes = calculate_loc_changes(repo_path, source, target)
    entropy = {}

    for filename, change in loc_changes.items():
        if change > 0:
            total_lines = sum(loc_changes.values())
            probability = change / total_lines
            entropy[filename] = -probability * math.log2(probability)

    print("Entropy:", entropy)
    return entropy
