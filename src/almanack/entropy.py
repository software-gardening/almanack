import math
from collections import Counter
from git_parser import calculate_loc_changes
def shannon_entropy_from_array(integers):
     # Get the frequency of each lines changed count
    freq = Counter(calculate_loc_changes.values())
    # Calculate the entropy
    entropy = 0.0
    total_files = len(calculate_loc_changes)
    for count in freq.values():
        prob = count / total_files
        entropy -= prob * math.log2(prob)
    print(entropy)
    return entropy