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

The ones that were not packages, could still be used as packages with [this instruction](https://github.com/Kiril-Mordan/reusables/blob/main/docs/module_from_raw_file.md).

## Content:
 
[module](python_modules/shouterlog.py) | [usage](docs/shouterlog.md) | [![PyPiVersion](https://img.shields.io/pypi/v/shouterlog)](https://pypi.org/project/shouterlog/) - Shouter Log

This class uses the logging module to create and manage a logger for displaying formatted messages.
It provides a method to output various types of lines and headers, with customizable message and line lengths.
The purpose is to be integrated into other classes that also use logger.

[module](python_modules/gridlooper.py) | [usage](docs/gridlooper.md) | [drawio: -flow](docs/gridlooper-flow.png) | [![PyPiVersion](https://img.shields.io/pypi/v/gridlooper)](https://pypi.org/project/gridlooper/) - Grid Looper

A tool to run experiments based on defined grid and function with single iteration.

[module](python_modules/package_auto_assembler.py) | [usage](docs/package_auto_assembler.md) | [drawio: -flow](docs/package_auto_assembler-flow.png) | [drawio: -usage](docs/package_auto_assembler-usage.png) | [![PyPiVersion](https://img.shields.io/pypi/v/package-auto-assembler)](https://pypi.org/project/package-auto-assembler/) - Package Auto Assembler

This tool is meant to streamline creation of single module packages.
Its purpose is to automate as many aspects of python package creation as possible,
to shorten a development cycle of reusable components, maintain certain standard of quality
for reusable code. It provides tool to simplify the process of package creatrion
to a point that it can be triggered automatically within ci/cd pipelines,
with minimal preparations and requirements for new modules.

[module](python_modules/retriever_tunner.py) | [usage](docs/retriever_tunner.md) - Retriever tunner

A simple tool to compare and tune retriever performance, given a desired ranking to strive for.
The goal is to provide a simple metric to measure how a given retriver is close to the 'ideal', generated for example
with a use of more expensive, slower or simply no-existant method.

[module](python_modules/google_drive_support.py) - Google Drive API Utilities Module

This module provides a set of functions for interacting with the Google Drive API.
It allows you to authenticate with the API, upload, download, and manage files and folders in Google Drive.

[module](python_modules/parameterframe.py) | [usage](docs/parameterframe.md) | [drawio: -flow](docs/parameterframe-flow.png) | [drawio: -schema](docs/parameterframe-schema.png) | [drawio: -usage](docs/parameterframe-usage.png) | [![PyPiVersion](https://img.shields.io/pypi/v/parameterframe)](https://pypi.org/project/parameterframe/) - Parameter frame

The module provides an interface for managing solution parameters.
It allows for the structured storage and retrieval of parameter sets from a database.

[module](python_modules/comparisonframe.py) | [usage](docs/comparisonframe.md) | [plantuml](docs/comparisonframe_plantuml.png) - Comparison Frame

Designed to automate and streamline the process of comparing textual data, particularly focusing on various metrics
such as character and word count, punctuation usage, and semantic similarity.
It's particularly useful for scenarios where consistent text analysis is required,
such as evaluating the performance of natural language processing models, monitoring content quality,
or tracking changes in textual data over time using manual evaluation.

[module](python_modules/mocker_db.py) | [usage](docs/mocker_db.md) | [drawio: -flow](docs/mocker_db-flow.png) | [release notes](release_notes/mocker_db.md) | [![PyPiVersion](https://img.shields.io/pypi/v/mocker-db)](https://pypi.org/project/mocker-db/) - MockerDB

A python module that contains mock vector database like solution built around
dictionary data type. It contains methods necessary to interact with this 'database',
embed, search and persist.

[module](python_modules/search_based_extractor.py) | [usage](docs/search_based_extractor.md) - Search Based Extractor

Utility to simplify webscraping by taking advantave of search and assumptions about html structure.
Extractor allows to find parent html element that contains searched term, record path to it in a file
and reuse that to scrape data with same html structure.

