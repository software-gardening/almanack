import pathlib
from almanack.LoC_tracker import calculate_loc_changes

def test_calculate_loc_changes(repository_paths: dict[str, pathlib.Path]):
    high_entropy_path = repository_paths["high_entropy"]
    low_entropy_path = repository_paths["low_entropy"]
    
    high_entropy_changes = calculate_loc_changes(high_entropy_path)
    low_entropy_changes = calculate_loc_changes(low_entropy_path)
    print("H"+str(high_entropy_changes))
    print("L"+str(low_entropy_changes))
    assert high_entropy_changes > low_entropy_changes, (
        f"Expected high entropy repository to have more changes. "
        f"High entropy changes: {high_entropy_changes}, Low entropy changes: {low_entropy_changes}"
    )