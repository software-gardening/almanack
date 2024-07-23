# __init__.py for software gardening almanack python package

from .book import read
from .entropy import aggregate_entropy_calculation, calculate_normalized_entropy
from .repo_helper import process_repository

# note: version placeholder is updated during build
# by poetry-dynamic-versioning.
__version__ = "0.0.0"
