# The Software Gardening Almanack

![PyPI - Version](https://img.shields.io/pypi/v/almanack)
[![Build Status](https://github.com/software-gardening/almanack/actions/workflows/pytest-tests.yml/badge.svg?branch=main)](https://github.com/software-gardening/almanack/actions/workflows/pytest-tests.yml?query=branch%3Amain)
![Coverage Status](https://raw.githubusercontent.com/software-gardening/almanack/main/media/coverage-badge.svg)

The Software Gardening Almanack is an open-source handbook of applied guidance and tools for sustainable software development and maintenance.
The Almanack is available both as a handbook and a Python package.

## Handbook

- __Online (HTML)__: https://software-gardening.github.io/almanack/
- __Offline (PDF)__: [software-gardening-almanack.pdf](https://software-gardening.github.io/almanack/software-gardening-almanack.pdf)

## Package

You can install the Almanack with the following:

```bash
# install from pypi
pip install almanack

# install directly from source
pip install git+https://github.com/software-gardening/almanack.git
```

Once installed, the Almanack can be used to analyze repositories for sustainable development practices.
Output from the Almanack includes metrics which are defined through `metrics.yml` as a Python dictionary (JSON-compatible) record structure.

For example:

```python
import almanack
import pandas as pd

# gather the almanack table using the almanack repo as a reference
almanack_table = almanack.metrics.data.get_table("path/to/repository")

# show the almanack table as a Pandas DataFrame
pd.DataFrame(almanack_table)
```

Alternatively, you can use the Almanack package as a command-line interface (CLI):

```bash
almanack path/to/repository
```

## Contributing

Please see our [`CONTRIBUTING.md`](CONTRIBUTING.md) document for more information on how to contribute to this project.

## Acknowledgements

This work was supported by the Better Scientific Software Fellowship Program, a collaborative effort of the U.S. Department of Energy (DOE), Office of Advanced Scientific Research via ANL under Contract DE-AC02-06CH11357 and the National Nuclear Security Administration Advanced Simulation and Computing Program via LLNL under Contract DE-AC52-07NA27344; and by the National Science Foundation (NSF) via SHI under Grant No. 2327079.
