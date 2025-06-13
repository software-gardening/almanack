# Understanding

```{figure} ../assets/garden-lattice-understanding-transfer.png
---
alt: Image showing two silhouettes with one showing transferrence of software
  idea to another.
---
_We transfer understanding of software projects in the form of documentation artifacts._
```

Shared understanding forms the heartbeat of any successful software project.
Peter Naur, in his work "Programming as Theory Building" (1985), emphasized that programming is fundamentally about building a shared theory of the project among all contributors {cite:p}`naur_programming_1985`.
Understanding encompasses not only the technical aspects of software, but also the collaborative and ethical dimensions that ensure a software project's growth and sustainability.
Just as a gardener must understand the needs of each plant to cultivate a thriving garden, contributors to a project must grasp its goals, structure, and community standards to foster a productive and harmonious environment.
Documentation, of which there are many different forms that we describe below, cultivates a shared understanding of a software project.

## Common files for shared understanding

In software development, certain files are expected to ensure project scope, clarity, collaboration, and legal compliance.
These files serve as the foundational elements that guide contributors and users, much like a well-tended garden benefits from clear paths and signs.
When present, these files are also correlated with increased rates of project success {cite:p}`coelho_why_2017`.

Historically, developers had written the following files in plain-text without formatting.
More recently, developers prefer [markdown](https://en.wikipedia.org/wiki/Markdown) to format the documents with rich styles and media.
GitHub, GitLab, and other software source control hosting platforms often automatically render markdown materials in HTML.

### README

The `README` file is the cornerstone of any repository, providing essential information about the project.
Its presence signifies a well-documented and accessible project, inviting contributors and users alike to understand and engage with the work.
A well-structured `README` will reference other pieces of important information that exist elsewhere, such as dependencies and other files we describe below.
A repository thrives when its purpose and usage are communicated through a `README` file, much like a garden benefits from a clear plan and understanding of its layout.

> "A good rule of thumb is to assume that the information contained within the README will be the only documentation your users read.
> For this reason, your README should include how to install and configure your software, where to find its full documentation, under what license it’s released, how to test it to ensure functionality, and acknowledgments." {cite:p}`lee_ten_2018`

For further reading on `README` file practices, see the following resources:

- [The Turing Way: Landing Page - README File](https://book.the-turing-way.org/project-design/pd-design-overview/project-repo/project-repo-readme)
- [GitHub: About `README`s](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes)
- [Makeareadme.com](https://www.makeareadme.com/)

### CONTRIBUTING

A `CONTRIBUTING` file outlines guidelines for how to add to the project.
Its presence fosters a welcoming environment for new contributors, ensuring that they have the necessary information to participate effectively.
In the same way that a garden flourishes when there's good understanding of how to provide care to the garden and gardeners, a project grows stronger when contributors are guided by clear and inclusive instructions.
The resulting nurturing environment fosters growth, resilience, and a sense of community, ensuring the project remains healthy and vibrant.

The `CONTRIBUTING` file should outline all development procedures that are specific to the project.
For example, the file might contain testing guidelines, linting/formatting expectations, release cadence, and more.
Consider writing this file from the perspective of both an outsider and a beginner: an outsider who might enhance your project by adding a new task or completing an existing task, and a beginner who seeks to understand your project from the ground up {cite:p}`treude_towards_2024`.

For further reading on `CONTRIBUTING` file practices, see the following resources:

- [GitHub: Setting guidelines for repository contributors](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/setting-guidelines-for-repository-contributors)
- [Mozilla: Wrangling Web Contributions: How to Build a CONTRIBUTING.md](https://mozillascience.github.io/working-open-workshop/contributing/)

### CODE_OF_CONDUCT

The `CODE_OF_CONDUCT` (CoC) file sets the standards for behavior within the project community.
Its presence signals a commitment to maintaining a respectful and inclusive environment for all participants.
It also may provide an outline for acceptable participation when it comes to conflicts of interest.
A CoC is a foundational document that defines community values, guides governance and moderation, and signals inclusivity within the project, particularly for vulnerable contributors. {cite:p}`damian_codes_2024`
A project community benefits from a shared understanding of respectful and supportive interactions, ensuring that all members can contribute positively, much like a garden requires a harmonious ecosystem to thrive.

For further reading and examples of `CODE_OF_CONDUCT` files, see the following:

- [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/)
- [Example: Python Software Foundation Code of Conduct](https://policies.python.org/python.org/code-of-conduct/)
- [Example: Rust Code of Conduct](https://www.rust-lang.org/policies/code-of-conduct)

### LICENSE

A `LICENSE` file specifies the terms under which the project's code can be used, modified, and shared.

> "When you make a creative work (which includes code), the work is under exclusive copyright by default. Unless you include a license that specifies otherwise, nobody else can copy, distribute, or modify your work without being at risk of take-downs, shake-downs, or litigation. Once the work has other contributors (each a copyright holder), “nobody” starts including you." {cite:p}`choosealicense_nopermission`.
> The presence of a `LICENSE` file is crucial for legal clarity, encourages the responsible use or distribution of the project, and is considered an indicator of project maturity{cite:p}`deekshitha_rsmm_2024`.

Just as a garden's health depends on understanding natural laws and respecting boundaries, a project's sustainability hinges on clear licensing that safeguards and empowers both creators and users, cultivating a culture of trust and collaboration.

For further reading and examples of `LICENSE` files, see the following:

- [OSF: Licensing](https://help.osf.io/article/148-licensing)
- [GitHub: Licensing a repository](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository)
- [Choosealicense.com](https://choosealicense.com/)
- [SPDX License List](https://spdx.org/licenses/)

## Project documentation

Common documentation files like `README`'s, `CONTRIBUTING` guides, and `LICENSE` files are only a start towards more specific project information.
Comprehensive project documentation is akin to a detailed gardener's notebook for a well-maintained project, illustrating how the project may be used and the guiding philosophy.
This includes in-depth explanations of the project's architecture, practical usage examples, application programming interface (API) references, and development workflows.
Oftentimes this type of documentation is provided through a "documentation website" or "docsite" to facilitate a user experience that includes a search bar, multimedia, and other HTML-enabled features.

Such documentation should strive to ensure that both novice and seasoned contributors can grasp the project's complexities and contribute effectively by delivering valuable information.
Writing valuable content entails conveying information that the code alone cannot communicate to the user {cite:p}`henney_97_2010`.
In addition to increased value from understanding, software tends to be more extensively utilized when developers offer more comprehensive documentation {cite:p}`afiaz_evaluation_2023`.
Just as a thriving garden benefits from meticulous care instructions and shared horticultural knowledge, a project flourishes when its documentation offers a clear and thorough guide to its inner workings, nurturing a collaborative and informed community.

Project documentation often exists within a dedicated `docs` directory where the materials may be created and versioned distinctly from other code.
Oftentimes this material will leverage a specific documentation tooling technology in alignment with the programming language(s) being used (for example, Python projects often leverage [Sphinx](https://www.sphinx-doc.org/en/master/)).
These tools often increase the utility of the output by styling the material with pre-built HTML themes, automating API documentation generation, and an ecosystem of plugins to help extend the capabilities of your documentation without writing new code.

For further reading and examples of deep Project documentation, see the following:

- [Berkeley Library: How to Write Good Documentation](https://guides.lib.berkeley.edu/how-to-write-good-documentation)
- [Write the Docs: Software documentation guide](https://www.writethedocs.org/guide/)
- [Overcoming Open Source Project Entry Barriers with a Portal for Newcomers](https://dl.acm.org/doi/10.1145/2884781.2884806)

```{bibliography}
---
style: unsrt
filter: docname in docnames
labelprefix: GLU
---
```
