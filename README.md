# Reusables

<a><img src="https://github.com/Kiril-Mordan/reusables/blob/main/docs/reuse_logo.png" width="35%" height="35%" align="right" /></a>

Contains pieces of code that have been generalized to the extent that they can be reused in other projects. The repository is designed to shorten the development cycle of single-module packages from the initial idea to a functioning alpha version accessible through PyPI.

## Usage

Modules in the reposity could be accessed from PyPI for the packages that reached that level. These meet the following criterias:

- passes linters threshold and unit tests if included
- passes vulnerability check of dependencies
- includes usage examples generated from corresponing .ipynb file
- contains short module level docstring
- contains __package_metadata__ (won't package without it)
- falls under common license

The ones that were not packaged, could still be used as packages with [this instruction](https://github.com/Kiril-Mordan/reusables/blob/main/docs/module_from_raw_file.md).


 
## Documentation
 
 
Links to the extended documentation of packaged modules, available through gh-pages:
 
- [`Gridlooper`](https://kiril-mordan.github.io/reusables/gridlooper)
- [`Mocker-db`](https://kiril-mordan.github.io/reusables/mocker_db)
- [`Package-auto-assembler`](https://kiril-mordan.github.io/reusables/package_auto_assembler)
- [`Parameterframe`](https://kiril-mordan.github.io/reusables/parameterframe)
- [`Shouterlog`](https://kiril-mordan.github.io/reusables/shouterlog)
 
Other content can be found [here](./docs/alternative_content.md).
