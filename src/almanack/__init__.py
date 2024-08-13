"""
__init__.py for software gardening almanack python package

Acknowledgements:

This work was supported by the Better Scientific Software Fellowship Program,
a collaborative effort of the U.S. Department of Energy (DOE), Office of
Advanced Scientific Research via ANL under Contract DE-AC02-06CH11357 and the
National Nuclear Security Administration Advanced Simulation and Computing
Program via LLNL under Contract DE-AC52-07NA27344; and by the National Science
Foundation (NSF) via SHI under Grant No. 2327079.
"""

from .book import read
from .processing.calculate_entropy import (
    calculate_aggregate_entropy,
    calculate_normalized_entropy,
)
from .processing.compute_data import process_repo_for_analysis

# note: version placeholder is updated during build
# by poetry-dynamic-versioning.
__version__ = "0.0.0"
