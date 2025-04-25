# Release notes

### 0.3.0

    - initial version of cache of llm classification performed during llm filtering step

    - integrating ollama and openai llm handlers for llm filter feature

    - upgrading older version of attrs to attrsx

### 0.2.7

    - minor fixes for initial llm filter

    - separate async search_database_async method

### 0.2.6

    - cosine similarity with torch

    - adding missing inputs for remote mocker in search_database method

### 0.2.5

    - simple cli for initializing optional config

    - wiring mocker connector into main mocker class

    - a single interface to interact with local and remote mocker

    - packaging existing mocker-db api routes with latest search options

### 0.2.4

    - making hnswlib optional dependency

### 0.2.3

    - providing flag to disable embedder initialization

    - disabling old cli intefrace

    - removing sentence_transformers from the list of default requirements so that SentenceTransformer needs to be provided externally if needed

### 0.2.2

    - option to get embedded field

    - initial llm filter

### 0.2.1

    - ability to return unique hash key for each record, previously inaccesible

### 0.2.0

    - precise keywords match with cutoff 1 and fuzzy match with < 1 through filters

    - keywords search with difflib

### 0.1.3

    - option to add embedding and distance to output list

    - option to remove output key while outputting the rest of keys

### 0.1.2

    - initital cli interface that allows to clone code from api version of mocker and run it

### 0.1.1

    - initial MockerConnect for using MockerDB API

### 0.0.12

    -  bugfix for similarity search through partly embedded data

### 0.0.11

    - more advanced filtering

### 0.0.10

    - fix for search without embeddings

### 0.0.6

    - fix for embedding storage

### 0.0.5

    - initial implementation of separate caching store for embeddings

### 0.0.4

    - updating hnswlib 0.7.0 -> 0.8.0 to fix vulnerabilities issue

    - fixing a bug with resetting mocker inner state properly after search

### 0.0.3

    - slightly improving logic of embedding with batches in parallel for sentence transformer embedder (default embedder)

    - updating desciption

### 0.0.2

    - better error handling in situations when data was not found with applied filters

### 0.0.1

    - initial version of MockerDB package that evolved from mock classes from redis into a standalone solution