# Reusables

<a><img src="https://github.com/Kiril-Mordan/reusables/blob/main/docs/reuse_logo.png" width="35%" height="35%" align="right" /></a>

Contains pieces of code that were generalized to a point where they can be reused in other projects, but due to their nature, do not deserve their own package.

## Usage

The most straight forward way to use the code without a need to either make a package or manually coping is to import from repository.

First define funtion for importing and then use it to import data with url to a particular point.

``` python
import requests
import importlib.util
import sys

def import_module_from_url(github_raw_url : str,
                           module_name : str) -> None:

    try:
        # Download the raw file
        response = requests.get(github_raw_url)
        response.raise_for_status()

        # Create a temporary module
        spec = importlib.util.spec_from_loader(module_name, loader=None)
        module = importlib.util.module_from_spec(spec)

        # Load the code into the module
        exec(response.text, module.__dict__)

        # Add the module to the current script's namespace
        sys.modules[module_name] = module

    except requests.exceptions.RequestException as e:
        print(f"Failed to download module from GitHub: {e}")
```

Find raw url to the python module and follow the example:

``` python
url = 'https://raw.githubusercontent.com/Kiril-Mordan/reusables/main/python_modules/google_drive_support.py'

import_module_from_url(github_raw_url=url,
                       module_name='google_drive_support')

from google_drive_support import get_google_drive_file_id, download_file, service_account, build
```

## Content:
 
[module](python_modules/redis_database_handler.py) - Redis Database Handler

A handler class for managing interactions with a Redis database. This class provides methods for initializing a logger,
establishing a connection with the Redis server, performing CRUD operations, and searching within the stored data based on embeddings.

[module](python_modules/package_auto_assembler.py) | [usage](docs/package_auto_assembler.md) - Package Auto Assembler

This tool is meant to streamline creation of single module packages.
Its purpose is to automate as many aspects of python package creation as possible,
to shorten a development cycle of reusable components, maintain certain standard of quality
for reusable code. It provides tool to simplify the process of package creatrion
to a point that it can be triggered automatically within ci/cd pipelines,
with minimal preparations and requirements for new modules.

[module](python_modules/shouterlog.py) | [usage](docs/shouterlog.md) - Shouter Log

This class uses the logging module to create and manage a logger for displaying formatted messages.
It provides a method to output various types of lines and headers, with customizable message and line lengths.
The purpose is to be integrated into other classes that also use logger.

[module](python_modules/retriever_tunner.py) - Retriever tunner

A simple tool to compare and tune retriever performance, given a desired ranking to strive for.
The goal is to provide a simple metric to measure how a given retriver is close to the 'ideal', generated for example
with a use of more expensive, slower or simply no-existant method.

[module](python_modules/search_based_extractor.py) | [usage](docs/search_based_extractor.md) - Search Based Extractor

Utility to simplify webscraping by taking advantave of search and assumptions about html structure.
Extractor allows to find parent html element that contains searched term, record path to it in a file
and reuse that to scrape data with same html structure.

[module](python_modules/mocker_db.py) | [usage](docs/mocker_db.md) - Mock Vector Db Handler

This class is a mock handler for simulating a vector database, designed primarily for testing and development scenarios.
It offers functionalities such as text embedding, hierarchical navigable small world (HNSW) search,
and basic data management within a simulated environment resembling a vector database.

[module](python_modules/google_drive_support.py) - Google Drive API Utilities Module

This module provides a set of functions for interacting with the Google Drive API.
It allows you to authenticate with the API, upload, download, and manage files and folders in Google Drive.

[module](python_modules/comparisonframe.py) | [usage](docs/comparisonframe.md) | [diagram](docs/comparisonframe.png) - Comparison Frame

Designed to automate and streamline the process of comparing textual data, particularly focusing on various metrics
such as character and word count, punctuation usage, and semantic similarity.
It's particularly useful for scenarios where consistent text analysis is required,
such as evaluating the performance of natural language processing models, monitoring content quality,
or tracking changes in textual data over time using manual evaluation.

