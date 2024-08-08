# __init__.py for software gardening almanack python package

from .book import read
from .processing.calculate_entropy import (
    calculate_aggregate_entropy,
    calculate_normalized_entropy,
)
from .processing.compute_data import process_repo_for_analysis

# note: version placeholder is updated during build
# by poetry-dynamic-versioning.
__version__ = "0.0.0"
