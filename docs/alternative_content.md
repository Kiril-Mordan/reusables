## Content:
 
 
[module](../python_modules/search_based_extractor.py) | [usage](../docs/search_based_extractor.md) - Search based extractor 

Search Based Extractor

Utility to simplify webscraping by taking advantave of search and assumptions about html structure.
Extractor allows to find parent html element that contains searched term, record path to it in a file
and reuse that to scrape data with same html structure.

[module](../python_modules/retriever_tunner.py) | [usage](../docs/retriever_tunner.md) - Retriever tunner 

Retriever tunner

A simple tool to compare and tune retriever performance, given a desired ranking to strive for.
The goal is to provide a simple metric to measure how a given retriver is close to the 'ideal', generated for example
with a use of more expensive, slower or simply no-existant method.

[module](../python_modules/prompt_strategies.py) - Prompt strategies 

PromptHandler prepares inputs for the llm requests.

[module](../python_modules/ollama.py) | [![PyPiVersion](https://img.shields.io/pypi/v/ollama)](https://pypi.org/project/ollama/) - Ollama 

OllamaHandlerAsync is a simple connector to ollama.AsyncClient
    meant to with LlmHandlerAsync in the role of llm_handler.

[module](../python_modules/comparisonframe.py) | [usage](../docs/comparisonframe.md) | [drawio: -flow](../docs/comparisonframe-flow.png) | [release notes](../release_notes/comparisonframe.md) | [![PyPiVersion](https://img.shields.io/pypi/v/comparisonframe)](https://pypi.org/project/comparisonframe/) - Comparisonframe 

Comparison Frame is designed to automate and streamline the process of comparing textual data, particularly focusing on various metrics
such as character and word count, punctuation usage, and semantic similarity.
It's particularly useful for scenarios where consistent text analysis is required,
such as evaluating the performance of natural language processing models, monitoring content quality,
or tracking changes in textual data over time using manual evaluation.

[module](../python_modules/google_drive_support.py) - Google drive support 

Google Drive API Utilities Module

This module provides a set of functions for interacting with the Google Drive API.
It allows you to authenticate with the API, upload, download, and manage files and folders in Google Drive.

