<img width="500" src="https://raw.githubusercontent.com/software-gardening/almanack/main/src/book/assets/software-gardening-almanack-logo.png?raw=true">

# The Software Gardening Almanack

![PyPI - Version](https://img.shields.io/pypi/v/almanack)
[![Build Status](https://github.com/software-gardening/almanack/actions/workflows/pytest-tests.yml/badge.svg?branch=main)](https://github.com/software-gardening/almanack/actions/workflows/pytest-tests.yml?query=branch%3Amain)
![Coverage Status](https://raw.githubusercontent.com/software-gardening/almanack/main/media/coverage-badge.svg)
[![Software DOI badge](https://zenodo.org/badge/DOI/10.5281/zenodo.14765835.svg)](https://doi.org/10.5281/zenodo.14765834)

The Software Gardening Almanack is an open-source handbook of applied guidance and tools for sustainable software development and maintenance.

The project entails two primary components:

- The __Almanack handbook__: the content found here helps educate, demonstrate, and evolve the concepts of sustainable software development.
- The __`almanack` package__: is a Python package which implements the concepts of the book to help improve software sustainability by generating organized metrics and running linting checks on repositories. The Python package may also be used as a [pre-commit hook to check](#pre-commit-hook) repositories for best practices.

Please see our [pavilion section of the book](https://software-gardening.github.io/almanack/garden-circle/pavilion.html) for presentations and other related materials for the Almanack.

## Handbook

- __Online (HTML)__: https://software-gardening.github.io/almanack/
- __Offline (PDF)__: [software-gardening-almanack.pdf](https://software-gardening.github.io/almanack/software-gardening-almanack.pdf)

## Package

### Install

You can install the Almanack with the following:

```bash
# install from pypi
pip install almanack

# install directly from source
pip install git+https://github.com/software-gardening/almanack.git
```

Once installed, the Almanack can be used to analyze repositories for sustainable development practices.
Output from the Almanack includes metrics which are defined through `metrics.yml` as a Python dictionary (JSON-compatible) record structure.

### Command-line Interface (CLI)

You can use the Almanack package as a command-line interface (CLI):

```bash
# generate a table of metrics based on a repository
almanack table path/to/repository

# perform linting-style checks on a repository
almanack check path/to/repository
```

### Pre-commit Hook

We provide [pre-commit](https://pre-commit.com/) hooks to enable you to run the Almanack as part of your automated checks for developing software projects.
Add the following to your [`pre-commit-config.yaml`](https://pre-commit.com/#2-add-a-pre-commit-configuration) in order to use the Almanack.

For example:

```yaml
# include this in your pre-commit-config.yaml
- repo: https://github.com/software-gardening/almanack
    rev: v0.1.1
    hooks:
    - id: almanack-check
```

### Python API

You can also use the Almanack through a Python API:

For example:

```python
import almanack
import pandas as pd

# gather the almanack table using the almanack repo as a reference
almanack_table = almanack.table("path/to/repository")

# show the almanack table as a Pandas DataFrame
pd.DataFrame(almanack_table)
```

### Example notebook

Please see [this example notebook](https://software-gardening.github.io/almanack/seed-bank/almanack-example/almanack-example.html) which demonstrates using the Almanack package.

### Batch processing many repositories

The `almanack batch` command runs the almanack check across many repositories in parallel and writes one parquet file (or one per batch) while optionally streaming progress to stdout.

```bash
# Run from a list (comma-separated) and write a single parquet
almanack batch results.parquet --repo_urls https://github.com/org/repo1,https://github.com/org/repo2 --max_workers 8

# Use threads (good for I/O-bound workloads) and split outputs per batch
almanack batch out_dir --repo_urls https://github.com/org/repo1,https://github.com/org/repo2 --executor thread --split_batches --batch_size 100

# Read repo URLs from a column in a provided parquet file
almanack batch results.parquet --parquet_path links.parquet --column github_link
```

Key options:

- `--executor`: `process` (default) or `thread`
- `--batch_size`: how many repos per batch (a small multiple of `max_workers` works well)
- `--split_batches`: an option to write one parquet file per batch into `output_path` (treated as a directory)
- `--collect_dataframe`: set to `False` to avoid returning a dataframe (only write to file)
- `--show_repo_progress`: shows progress per repository
- `--show_batch_progress`: shows progress per batch (sets of repos)
- `--show_errors`: emit any errors from the almanack processing

Python API example:

```python
from concurrent.futures import ThreadPoolExecutor
from almanack import process_repositories_batch

repos = ["https://github.com/org/repo1", "https://github.com/org/repo2"]

# Single parquet
df = process_repositories_batch(
    repos,
    output_path="almanack_results.parquet",
    max_workers=8,
    executor_cls=ThreadPoolExecutor,  # threads are notebook-friendly / I/O-friendly
)

# Per-batch files, no in-memory DataFrame
process_repositories_batch(
    repos,
    output_path="batch_outputs",
    split_batches=True,
    collect_dataframe=False,
    batch_size=100,
    max_workers=16,
)
```

### GitHub API performance

The Almanack uses GitHub’s API to gather certain metrics.
Anonymous API requests have extremely low rate limits—once hit, requests are throttled and batch jobs slow down.
Export a [personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens) as `GITHUB_TOKEN` before running any CLI or Python workflows to raise the per-hour quota:

```bash
export GITHUB_TOKEN=ghp_yourtokenhere
```

Commands launched from the same shell automatically reuse the token, so your GitHub requests complete faster and more reliably.

## Contributing

Please see our [`CONTRIBUTING.md`](CONTRIBUTING.md) document for more information on how to contribute to this project.

## Acknowledgements

This work was supported by the Better Scientific Software Fellowship Program, a collaborative effort of the U.S. Department of Energy (DOE), Office of Advanced Scientific Research via ANL under Contract DE-AC02-06CH11357 and the National Nuclear Security Administration Advanced Simulation and Computing Program via LLNL under Contract DE-AC52-07NA27344; and by the National Science Foundation (NSF) via SHI under Grant No. 2327079.
