# Contributing

First of all, thank you for contributing to the Software Gardening Almanac! 🎉 💯 🪴
We're absolutely grateful for the kindness of your effort applied to grow this project into the best that it can be.

This document contains guidelines on how to most effectively contribute to this project.

If you are stuck or would like clarifications, please feel free to ask any questions or for help.

## Code of conduct

This project is governed by our [Code of Conduct (CoC) policy](https://github.com/software-gardening/almanac?tab=coc-ov-file) (located [here](https://github.com/software-gardening/.github/blob/main/CODE_OF_CONDUCT.md)).
By participating, you are expected to uphold this code.
Please report unacceptable behavior by following the procedures listed under the [CoC Enforcement section](https://github.com/software-gardening/almanac?tab=coc-ov-file#enforcement).

## Security

Please see our [Security policy](https://github.com/software-gardening/almanac?tab=security-ov-file) (located [here](https://github.com/software-gardening/.github/blob/main/SECURITY.md)) for more information on security practices and recommendations associated with this project.

## Quick links

- Documentation: <https://github.com/software-gardening/almanac>
- Issue tracker: <https://github.com/software-gardening/almanac/issues>

## Process

### Reporting bugs or suggesting enhancements

We’re deeply committed to a smooth and intuitive user experience which helps people benefit from the content found within this project.
This commitment requires a good relationship and open communication with our users.

We encourage you to report bugs or propose enhancements to improve the Software Gardening Almanac as a [GitHub issue](https://docs.github.com/en/issues/tracking-your-work-with-issues/creating-an-issue) associated with the repository.

First, figure out if your proposal is already implemented by reading existing issues or pull requests!
Next, check the issues (<https://github.com/software-gardening/almanac/issues>) to see if someone else has already reported the bug or proposed the enhancement you have in mind.
If you do find the suggestion, please comment on the existing issue noting that you are also interested in the functionality.
If you do not find the suggestion, please open a new issue and document the specific enhancement and why it would be helpful for your particular use case.

Specifically, the following may help when it comes to addressing the issue:

- The version of the Software Gardening Almanac you're referencing.
- Specific error messages or how the issue exhibits itself.
- Operating system (e.g. MacOS, Windows, etc.)
- Device type (e.g. laptop, phone, etc.)
- Any examples of similar capabilities

### Your first code contribution

Contributing code for the first time can be a daunting task.
However, in our community, we strive to be as welcoming as possible to newcomers, while ensuring sustainable software development practices.

The first thing to figure out is exactly what you’re going to contribute!
We describe all future work as individual [github issues](https://github.com/software-gardening/almanac/issues).
For first time contributors we have specifically labeled as [good first issue](https://github.com/software-gardening/almanac/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22).

If you want to contribute code that we haven’t already outlined, please start a discussion in a new issue before writing any code.
A discussion will clarify the new code and reduce merge time.
Plus, it’s possible your contribution belongs in a different code base, and we do not want to waste your time (or ours)!

### Pull requests

After you’ve decided to contribute code and have written it up, please file a pull request.
We specifically follow a [forked pull request model](https://docs.github.com/en/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request-from-a-fork).
Please create a fork of Software Gardening Almanac repository, clone the fork, and then create a new, feature-specific branch.
Once you make the necessary changes on this branch, you should file a pull request to incorporate your changes into the main The Software Gardening Almanac repository.

The content and description of your pull request are directly related to the speed at which we are able to review, approve, and merge your contribution into The Software Gardening Almanac.
To ensure an efficient review process please perform the following steps:

1. Follow all instructions in the [pull request template](https://github.com/software-gardening/almanac/blob/main/.github/PULL_REQUEST_TEMPLATE.md)
1. Triple check that your pull request is adding _one_ specific feature. Small, bite-sized pull requests move so much faster than large pull requests.
1. After submitting your pull request, ensure that your contribution passes all status checks (e.g. passes all tests)

Pull request review and approval is required by at least one project maintainer to merge.
We will do our best to review the code additions in a timely fashion.
Ensuring that you follow all steps above will increase our speed and ability to review.
We will check for accuracy, style, code coverage, and scope.

### Git commit messages

For all commit messages, please use a short phrase that describes the specific change.
For example, “Add feature to check normalization method string” is much preferred to “change code”.
When appropriate, reference issues (via `#` plus number) .

## Development

### Overview

The Software Gardening Almanac is primarily written in [Python](https://www.python.org/) through [Jupyter Book](https://jupyterbook.org/) with related environments managed by Python [Poetry](https://python-poetry.org/).
We use [GitHub actions](https://docs.github.com/en/actions) for automated tests.

### Getting started

To enable local development, perform the following steps.

1. [Install Python](https://www.python.org/downloads/)
1. [Install Poetry](https://python-poetry.org/docs/#installation)
1. [Install Poetry Environment](https://python-poetry.org/docs/basic-usage/#installing-dependencies): `poetry install`

### Linting

Work added to this repo is automatically checked using [pre-commit](https://pre-commit.com/) via [GitHub Actions](https://docs.github.com/en/actions).
Pre-commit can work alongside your local [git with git-hooks](https://pre-commit.com/index.html#3-install-the-git-hook-scripts)
After [installing pre-commit](https://pre-commit.com/#installation) within your development environment, the following command also can perform the same checks:

```sh
% pre-commit run --all-files
```

## Attribution

Portions of this contribution guide were sourced from [pyctyominer](https://github.com/cytomining/pycytominer/blob/master/CONTRIBUTING.md).
Many thanks go to the developers and contributors of that repository.
