# Understanding

```{figure} ../assets/garden-lattice-understanding-transfer.png
---
alt: Image showing two silhouettes with one showing transferrence of software idea to another.
---
_We transfer understanding of software projects in the form of documentation artifacts._
```

Shared understanding forms the heartbeat of any successful software project.
Peter Naur, in his work "Programming as Theory Building" (1985), emphasized that programming is fundamentally about building a shared theory of the project among all contributors {cite:p}`naur_programming_1985`.
Understanding encompasses not only the technical aspects but also the collaborative and ethical dimensions that ensure a project's growth and sustainability.
Just as a gardener must understand the needs of each plant to cultivate a thriving garden, contributors to a project must grasp its goals, structure, and community standards to foster a productive and harmonious environment.
We present the following as beginnings towards shared understanding in a project, recognizing that digital files do not equate to human cognitition.

## Common files for shared understanding

In the realm of software development, certain files are commonly expected within a repository to ensure clarity, collaboration, and legal compliance.
These files serve as the foundational elements that guide contributors and users, much like a well-tended garden benefits from clear pathways and signs.
They also are correlated with increased rates of project success when present {cite:p}`coelho_why_2017`.
Historically the following files were written in plain-text without formatting.
More recently [markdown](https://en.wikipedia.org/wiki/Markdown) has become the preferred method of writing these files to help format the documents with styles and media.
GitHub, GitLab, and other software source control hosting platforms often automatically render markdown materials in HTML.

### README

The `README` file is the cornerstone of any repository, providing essential information about the project.
Its presence signifies a well-documented and accessible project, inviting contributors and users alike to understand and engage with the work.
A repository thrives when its purpose and usage are communicated through a `README` file, much like a garden benefits from a clear plan and understanding of its layout.

> "A good rule of thumb is to assume that the information contained within the README will be the only documentation your users read.
> For this reason, your README should include how to install and configure your software, where to find its full documentation, under what license it’s released, how to test it to ensure functionality, and acknowledgments.
> Furthermore, you should include your quickstart guide (as introduced in Rule 3) in your README." {cite:p}`lee_ten_2018`

For further reading on `README` file practices, see the following resources:

- [The Turing Way: Landing Page - README File](https://book.the-turing-way.org/project-design/project-repo/project-repo-readme.html)
- [GitHub: About `README`s](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes)
- [Makeareadme.com](https://www.makeareadme.com/)

### CONTRIBUTING

A `CONTRIBUTING` file outlines the guidelines for contributing to the project.
Its presence fosters a welcoming environment for new contributors, ensuring that they have the necessary information to participate effectively.
In the same way that a garden flourishes when there's good understanding of roles and how to care for one another, a project grows stronger when contributors are guided by clear and inclusive instructions.

All development procedures which are specific to the project should be outlined within the `CONTRIBUTING` file (for example, testing and linting expectations, release cadence, etc.).
Consider writing this documentation for each project from the standpoint of an outsider or beginner who may be trying to add a new task, understand the project, or complete an existing task {cite:p}`treude_towards_2024`.

For further reading on `CONTRIBUTING` file practices, see the following resources:

- [GitHub: Setting guidelines for repository contributors](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/setting-guidelines-for-repository-contributors)
- [Mozilla: Wrangling Web Contributions: How to Build a CONTRIBUTING.md](https://mozillascience.github.io/working-open-workshop/contributing/)

### CODE_OF_CONDUCT

The `CODE_OF_CONDUCT` (CoC) files set the standards for behavior within the project community.
Its presence is a commitment to maintaining a respectful and inclusive environment for all participants.
It also may provide an outline for acceptable participation when it comes to conflicts of interest or similar.
"CoCs are a place to express and define shared community values in OSS projects, an important governance document for moderation, and an indicator of project inclusivity and safety, especially for vulnerable contributors" {cite:p}`damian_codes_2024`
A project community benefits from a shared understanding of respectful and supportive interactions, ensuring that all members can contribute positively, much like a garden requires a harmonious ecosystem to thrive.

For further reading and examples of `CODE_OF_CONDUCT` files, see the following:

- [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/)
- [Example: Python Software Foundation Code of Conduct](https://policies.python.org/python.org/code-of-conduct/)
- [Example: Rust Code of Conduct](https://www.rust-lang.org/policies/code-of-conduct)

### LICENSE

A `LICENSE` file specifies the terms under which the project's code can be used, modified, and shared.
> "When you make a creative work (which includes code), the work is under exclusive copyright by default. Unless you include a license that specifies otherwise, nobody else can copy, distribute, or modify your work without being at risk of take-downs, shake-downs, or litigation. Once the work has other contributors (each a copyright holder), “nobody” starts including you." {cite:p}`choosealicense_nopermission`.
The presence of a `LICENSE` file is crucial for legal clarity, encourages the responsible use or distribution of the project, and is considered an indicator of project maturity{cite:p}`deekshitha_rsmm_2024`.

Similar to how a garden's health depends on understanding the rules of nature and respecting boundaries, a project's sustainability relies on clear licensing that protects both the creators and users, fostering a culture of trust and collaboration.

For further reading and examples of `LICENSE` files, see the following:

- [OSF: Licensing](https://help.osf.io/article/148-licensing)
- [GitHub: Licensing a repository](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository)
- [Choosealicense.com](https://choosealicense.com/)

## Project documentation

Common documentation files like `README`'s, `CONTRIBUTING` guides, and `LICENSE` files are only a start towards more specific project information.
Comprehensive project documentation is akin to a detailed gardener's notebook for a well-maintained project, illustrating how the project may be used and guiding philosophy.
This includes in-depth explanations of the project's architecture, practical usage examples, API references, and development workflows.
Such documentation should strive to go above and beyond to ensure that both novice and seasoned contributors can grasp the project's complexities and contribute effectively.
Just as a thriving garden benefits from meticulous care instructions and shared horticultural knowledge, a project flourishes when its documentation offers a clear and thorough guide to its inner workings, nurturing a collaborative and informed community.

Project documentation often exists within a dedicated `docs` directory where the materials may be created and versioned distinctly from other code.

```{bibliography}
---
style: unsrt
filter: docname in docnames
labelprefix: GLU
---
```
