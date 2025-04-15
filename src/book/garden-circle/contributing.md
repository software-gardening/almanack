# Contributing

First of all, thank you for contributing to the Software Gardening Almanack! 🎉 💯 🪴
We're so grateful for the kindness of your effort applied to grow this project into the best that it can be.

This document contains guidelines on how to most effectively contribute to this project.

If you would like clarifications, please feel free to ask any questions or for help.
We suggest asking for help from GitHub where you may need it (for example, in a GitHub issue or a pull request) by ["at (@) mentioning"](https://github.blog/2011-03-23-mention-somebody-they-re-notified/) a Software Gardening Almanack maintainer (for example, `@username`).

## Code of conduct

Our [Code of Conduct (CoC) policy](https://github.com/software-gardening/almanack?tab=coc-ov-file) (located [here](https://github.com/software-gardening/.github/blob/main/CODE_OF_CONDUCT.md)) governs this project.
By participating in this project, we expect you to uphold this code.
Please report unacceptable behavior by following the procedures listed under the [CoC Enforcement section](https://github.com/software-gardening/almanack?tab=coc-ov-file#enforcement).

## Security

Please see our [Security policy](https://github.com/software-gardening/almanack?tab=security-ov-file) (located [here](https://github.com/software-gardening/.github/blob/main/SECURITY.md)) for more information on security practices and recommendations associated with this project.

## Quick links

- Documentation: <https://github.com/software-gardening/almanack>
- Issue tracker: <https://github.com/software-gardening/almanack/issues>

## Process

### Reporting bugs or suggesting enhancements

We’re deeply committed to a smooth and intuitive user experience which helps people benefit from the content found within this project.
This commitment requires a good relationship and open communication with our users.

We encourage you to file a [GitHub issue](https://docs.github.com/en/issues/tracking-your-work-with-issues/creating-an-issue) to report bugs or propose enhancements to improve the Software Gardening Almanack.

First, figure out if your idea is already implemented by reading existing issues or pull requests!
Check the issues (<https://github.com/software-gardening/almanack/issues>) and pull requests (<https://github.com/software-gardening/almanack/pulls>) to see if someone else has already documented or began implementation of your idea.
If you do find your idea in an existing issue, please comment on the existing issue noting that you are also interested in the functionality.
If you do not find your idea, please open a new issue and document why it would be helpful for your particular use case.

Please also provide the following specifics:

- The version of the Software Gardening Almanack you're referencing.
- Specific error messages or how the issue exhibits itself.
- Operating system (e.g. MacOS, Windows, etc.)
- Device type (e.g. laptop, phone, etc.)
- Any examples of similar capabilities

### Your first code contribution

Contributing code for the first time can be a daunting task.
However, in our community, we strive to be as welcoming as possible to newcomers, while ensuring sustainable software development practices.

The first thing to figure out is specifically what you’re going to contribute!
We describe all future work as individual [GitHub issues](https://github.com/software-gardening/almanack/issues).
For first time contributors we have specifically labeled as [good first issue](https://github.com/software-gardening/almanack/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22).

If you want to contribute code that we haven’t already outlined, please start a discussion in a new issue before writing any code.
A discussion will clarify the new code and reduce merge time.
Plus, it’s possible your contribution belongs in a different code base, and we do not want to waste your time (or ours)!

### Pull requests

After you’ve decided to contribute code and have written it up, please file a pull request.
We specifically follow a [forked pull request model](https://docs.github.com/en/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request-from-a-fork).
Please create a fork of Software Gardening Almanack repository, clone the fork, and then create a new, feature-specific branch.
Once you make the necessary changes on this branch, you should file a pull request to incorporate your changes into the main The Software Gardening Almanack repository.

The content and description of your pull request are directly related to the speed at which we are able to review, approve, and merge your contribution into The Software Gardening Almanack.
To ensure an efficient review process please perform the following steps:

1. Follow all instructions in the [pull request template](https://github.com/software-gardening/almanack/blob/main/.github/PULL_REQUEST_TEMPLATE.md)
1. Triple check that your pull request is adding _one_ specific feature. Small, bite-sized pull requests move so much faster than large pull requests.
1. After submitting your pull request, ensure that your contribution passes all status checks (e.g. passes all tests)

We require pull request review and approval by at least one project maintainer in order to merge.
We will do our best to review the code additions in as soon as we can.
Ensuring that you follow all steps above will increase our speed and ability to review.
We will check for accuracy, style, code coverage, and scope.

### Git commit messages

For all commit messages, please use a short phrase that describes the specific change.
For example, “Add feature to check normalization method string” is much preferred to “change code”.
When appropriate, reference issues (via `#` plus number) .

## Development

### Overview

We write and develop the Software Gardening Almanack in [Python](https://www.python.org/) through [Jupyter Book](https://jupyterbook.org/) with related environments managed by Python [Poetry](https://python-poetry.org/).
We use [Node](https://nodejs.org) and [NPM](https://www.npmjs.com/) dependencies to assist development activities (such as performing linting checks or other capabilities).
We use [GitHub actions](https://docs.github.com/en/actions) for [CI/CD](https://en.wikipedia.org/wiki/CI/CD) procedures such as automated tests.

### Getting started

To enable local development, perform the following steps.

1. [Install Python](https://www.python.org/downloads/) (suggested: use [`pyenv`](https://github.com/pyenv/pyenv) for managing Python versions)
1. [Install Poetry](https://python-poetry.org/docs/#installation)
1. [Install Poetry environment](https://python-poetry.org/docs/basic-usage/#installing-dependencies): `poetry install`
1. [Install Node](https://nodejs.org/en/download) (suggested: use [`nvm`](https://github.com/nvm-sh/nvm) for managing Node versions)
1. [Install Node environment](https://docs.npmjs.com/cli/v9/commands/npm-install): `npm install`
1. [Install Vale dependencies](https://vale.sh/docs/cli): `poetry run vale sync`
1. [Optional: install book PDF rendering dependencies](https://jupyterbook.org/en/stable/advanced/pdf.html): `poetry run playwright install --with-deps chromium`

### Development Tasks

We use [Poe the Poet](https://poethepoet.natn.io/) to define common development tasks, which simplifies repeated commands.
We include Poe the Poet as a Python Poetry `dev` group dependency, which users access through the Poetry environment.
Please see the [`pyproject.toml`](https://github.com/software-gardening/almanack/blob/main/pyproject.toml) file's `[tool.poe.tasks]` table for a list of available tasks.

For example:

```shell
# example of how Poe the Poet commands may be used.
poetry run poe <task_name>

# example of a task which runs jupyter-book build for the project
poetry run poe build-book
```

### Linting

[pre-commit](https://pre-commit.com/) automatically checks all work added to this repository.
We implement these checks using [GitHub Actions](https://docs.github.com/en/actions).
Pre-commit can work alongside your local [git with git-hooks](https://pre-commit.com/index.html#3-install-the-git-hook-scripts)
After [installing pre-commit](https://pre-commit.com/#installation) within your development environment, the following command performs the same checks:

```sh
% pre-commit run --all-files
```

We strive to provide comments about each pre-commit check within the [`.pre-commit-config.yaml`](https://github.com/software-gardening/almanack/blob/main/.pre-commit-config.yaml) file.
Comments are provided within the file to make sure we single-source documentation where possible, avoiding possible drift between the documentation and the code which runs the checks.

### Automated CI/CD with GitHub Actions

We use [GitHub Actions](https://docs.github.com/en/actions) to help perform automated [CI/CD](https://en.wikipedia.org/wiki/CI/CD) as part of this project.
GitHub Actions involves defining [workflows](https://docs.github.com/en/actions/using-workflows) through [YAML files](https://en.wikipedia.org/wiki/YAML).
These workflows include one or more [jobs](https://docs.github.com/en/actions/using-jobs) which are collections of individual processes (or steps) which run as part of a job.
We define GitHub Actions work under the [`.github`](https://github.com/software-gardening/almanack/tree/main/.github) directory.
We suggest the use of [`act`](https://github.com/nektos/act) to help test GitHub Actions work during development.

### Releases

We utilize [semantic versioning](https://en.wikipedia.org/wiki/Software_versioning#Semantic_versioning) ("semver") to distinguish between major, minor, and patch releases.
We publish source code by using [GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases) available [here](https://github.com/software-gardening/almanack/releases).
Contents of the book are distributed as both a [website](https://software-gardening.github.io/almanack/) and [PDF](https://software-gardening.github.io/almanack/software-gardening-almanack.pdf).
We distribute a Python package through the [Python Packaging Index (PyPI)](https://pypi.org/) available [here](https://pypi.org/project/almanack/) which both includes and provides tooling for applying the book's content.

Publishing Software Gardening Almanack releases involves several manual and automated steps.
See below for an overview of how this works.

#### Version specifications

We follow [semantic version](https://en.wikipedia.org/wiki/Software_versioning#Semantic_versioning) (semver) specifications with this project through the following technologies.

- [`poetry-dynamic-versioning`](https://github.com/mtkennerly/poetry-dynamic-versioning) leveraging [`dunamai`](https://github.com/mtkennerly/dunamai) creates version data based on [git tags](https://git-scm.com/book/en/v2/Git-Basics-Tagging) and commits.
- [GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases) automatically create git tags and source code collections available from the GitHub repository.
- [`release-drafter`](https://github.com/release-drafter/release-drafter) infers and describes changes since last release within automatically drafted GitHub Releases after pull requests are merged (draft releases are published as decided by maintainers).

#### Release process

1. Open a pull request and use a repository label for `release-<semver release type>` to label the pull request for visibility with [`release-drafter`](https://github.com/release-drafter/release-drafter) (for example, see [almanack#43](https://github.com/software-gardening/almanack/pull/43) as a reference of a semver patch update).
1. On merging the pull request for the release, a [GitHub Actions workflow](https://docs.github.com/en/actions/using-workflows) defined in `draft-release.yml` leveraging [`release-drafter`](https://github.com/release-drafter/release-drafter) will draft a release for maintainers.
1. The draft GitHub release will include a version tag based on the GitHub PR label applied and `release-drafter`.
1. Make modifications as necessary to the draft GitHub release, then publish the release (the draft release does not normally need additional modifications).
1. On publishing the release, another GitHub Actions workflow defined in `publish-pypi.yml` will automatically build and deploy the Python package to PyPI (utilizing the earlier modified `pyproject.toml` semantic version reference for labeling the release).
1. Each GitHub release will trigger a [Zenodo GitHub integration](https://docs.github.com/en/repositories/archiving-a-github-repository/referencing-and-citing-content#issuing-a-persistent-identifier-for-your-repository-with-zenodo) which creates a new Zenodo record and unique DOI.

## Citations

We create a unique DOI per release through the [Zenodo GitHub integration](https://docs.github.com/en/repositories/archiving-a-github-repository/referencing-and-citing-content#issuing-a-persistent-identifier-for-your-repository-with-zenodo).
As part of this we also use a special DOI provided from Zenodo to reference the latest record on each new release.
Zenodo outlines how this works within their [versioning documentation](https://zenodo.org/help/versioning).

The DOI and other citation metadata are stored within a [`CITATION.cff` file](https://github.com/citation-file-format/citation-file-format).
Our `CITATION.cff` is the primary source of citation information in correspondence with this project.
The `CITATION.cff` file is used within a sidebar [integration through the GitHub web interface](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-citation-files) to enable people to directly cite this project.

## Attribution

We sourced portions of this contribution guide from [`pyctyominer`](https://github.com/cytomining/pycytominer/blob/main/CONTRIBUTING.md).
Big thanks go to the developers and contributors of that repository.
