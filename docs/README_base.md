# Reusables

<a><img src="https://github.com/Kiril-Mordan/reusables/blob/main/docs/reuse_logo.png" width="35%" height="35%" align="right" /></a>

Contains pieces of code that have been generalized to the extent that they can be reused in other projects. The repository is designed to shorten the development cycle of single-module packages from the initial idea to a functioning alpha version accessible on PyPI.

## Usage

Modules in the reposity could be accessed from PyPI for the packages that reached that level. These meet the following criterias:

- passes linters threshold and unit tests if included
- includes usage examples generated from corresponing .ipynb file
- contains a short description included in README
- contains __package_metadata__ (won't package without it)
- falls under common license

The ones that were not packages, could still be used as packages with [this instruction]("https://github.com/Kiril-Mordan/reusables/blob/main/docs/module_from_raw_file.md").

## Content:
