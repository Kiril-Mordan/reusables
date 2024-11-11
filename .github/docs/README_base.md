# Reusables

<a><img src="https://raw.githubusercontent.com/Kiril-Mordan/reusables/refs/heads/main/.github/docs/reuse_logo.png" width="35%" height="35%" align="right" /></a>

Contains pieces of code that have been generalized to the extent that they can be reused in other projects. The repository is designed to shorten the development cycle of single-module packages from the initial idea to a functioning alpha version accessible through PyPI.

Its ci/cd pipeline contains tools to package not only simple python modules, but cli tools with click, static documnentation with mkdocs, routes for fastapi applications and files within a package as artifacts, that could be extracted from that package later.

## Usage

Modules in the reposity could be accessed from PyPI for the packages that reached that level. These meet the following criterias:

- passes linters threshold and unit tests if included
- passes vulnerability check of dependencies
- includes usage examples generated from corresponing .ipynb file
- contains short module level docstring
- contains `__package_metadata__` (won't package without it)
- falls under common [`license`](https://github.com/Kiril-Mordan/reusables/blob/main/LICENSE)



