# Mocker DB

This class is a mock handler for simulating a vector database, designed primarily for testing and development scenarios.
It offers functionalities such as text embedding, hierarchical navigable small world (HNSW) search,
and basic data management within a simulated environment resembling a vector database.



```python
# import sys
# sys.path.append('../')
import numpy as np
from mocker_db import MockerDB, SentenceTransformerEmbedder, MockerSimilaritySearch
```

## Usage examples

The examples contain:
1. Inserting values into the database
2. Seaching and retrieving values from the database
3. Removing values from the database
4. Testing the HNSW Search Algorithm


### 1. Inseting values into the database


```python
# Initialization
handler = MockerDB(
    # optional
    embedder_params = {'model_name_or_path' : 'paraphrase-multilingual-mpnet-base-v2',
                        'processing_type' : 'batch',
                        'tbatch_size' : 500},
    embedder = SentenceTransformerEmbedder,
    ## optional/ for similarity search
    similarity_search = MockerSimilaritySearch,
    return_keys_list = None,
    search_results_n = 3,
    similarity_search_type = 'linear',
    similarity_params = {'space':'cosine'},
    ## optional/ inputs with defaults
    file_path = "./mock_persist",
    persist = True,
    embedder_error_tolerance = 0.0
)
# Initialize empty database
handler.establish_connection()
```


```python
# Insert Data
values_list = [
    {"text": "Sample text 1",
     "text2": "Sample text 1"},
    {"text": "Sample text 2",
     "text2": "Sample text 2"}
]
handler.insert_values(values_list, "text")
print(f"Items in the database {len(handler.data)}")
```

    Items in the database 2


### 2. Seaching and retrieving values from the database

- get all keys


```python
results = handler.search_database(
    query = "text",
    filter_criteria = {
        "text" : "Sample text 1",
    }
)
print([{k: str(v)[:30] + "..." for k, v in result.items()} for result in results])
```

    [{'text': 'Sample text 1...', 'text2': 'Sample text 1...'}]


- get all keys with keywords search


```python
results = handler.search_database(
    query = "text",
    # when keyword key is provided filter is used to pass keywords
    filter_criteria = {
        "text" : ["1"],
    },
    keyword_check_keys = ['text'],
    # percentage of filter keyword allowed to be different
    keyword_check_cutoff = 1,
    return_keys_list=['text']
)
print([{k: str(v)[:30] + "..." for k, v in result.items()} for result in results])
```

    [{'text': 'Sample text 1...'}]


- get all key - text2


```python
results = handler.search_database(
    query = "text",
    filter_criteria = {
        "text" : "Sample text 1",
    },
    return_keys_list=["-text2"])
print([{k: str(v)[:30] + "..." for k, v in result.items()} for result in results])
```

    [{'text': 'Sample text 1...'}]


- get all keys + distance


```python
results = handler.search_database(
    query = "text",
    filter_criteria = {
        "text" : "Sample text 1"
    },
    return_keys_list=["+&distance"]
)
print([{k: str(v)[:30] + "..." for k, v in result.items()} for result in results])
```

    [{'text': 'Sample text 1...', 'text2': 'Sample text 1...', '&distance': '0.6744726...'}]


- get distance


```python
results = handler.search_database(
    query = "text",
    filter_criteria = {
        "text" : "Sample text 1"
    },
    return_keys_list=["&distance"]
)
print([{k: str(v)[:30] + "..." for k, v in result.items()} for result in results])
```

    [{'&distance': '0.6744726...'}]


- get all keys + embeddings


```python
results = handler.search_database(
    query = "text",
    filter_criteria = {
        "text" : "Sample text 1"
    },
    return_keys_list=["+embedding"]
)
print([{k: str(v)[:30] + "..." for k, v in result.items()} for result in results])
```

    [{'text': 'Sample text 1...', 'text2': 'Sample text 1...', 'embedding': '[-4.94664945e-02 -2.38676071e-...'}]


- get embeddings


```python
results = handler.search_database(
    query = "text",
    filter_criteria = {
        "text" : "Sample text 1"
    },
    return_keys_list=["embedding"]
)
print([{k: str(v)[:30] + "..." for k, v in result.items()} for result in results])

```

    [{'embedding': '[-4.94664945e-02 -2.38676071e-...'}]


- get embeddings and embedded field


```python
results = handler.search_database(
    query = "text",
    filter_criteria = {
        "text" : "Sample text 1"
    },
    return_keys_list=["embedding", "+&embedded_field"]
)
print([{k: str(v)[:30] + "..." for k, v in result.items()} for result in results])

```

    [{'embedding': '[-4.94664945e-02 -2.38676071e-...', '&field_to_embed': 'text...'}]


### 3. Removing values from the database


```python
print(f"Items in the database {len(handler.data)}")
handler.remove_from_database(filter_criteria = {"text": "Sample text 1"})
print(f"Items left in the database {len(handler.data)}")

```

    Items in the database 2
    Items left in the database 1


### 4. Testing the HNSW Search Algorithm


```python
mss = MockerSimilaritySearch(
    # optional
    search_results_n = 3,
    similarity_params = {'space':'cosine'},
    similarity_search_type ='linear'
)

ste = SentenceTransformerEmbedder(# optional / adaptor parameters
                                  processing_type = '',
                                  tbatch_size = 500,
                                  max_workers = 2,
                                  # sentence transformer parameters
                                  model_name_or_path = 'paraphrase-multilingual-mpnet-base-v2',)
```


```python
# Create embeddings
embeddings = [ste.embed("example1"), ste.embed("example2")]


# Assuming embeddings are pre-calculated and stored in 'embeddings'
data_with_embeddings = {"record1": {"embedding": embeddings[0]}, "record2": {"embedding": embeddings[1]}}
handler.data = data_with_embeddings

# HNSW Search
query_embedding = embeddings[0]  # Example query embedding
labels, distances = mss.hnsw_search(query_embedding, np.array(embeddings), k=1)
print(labels, distances)

```

    [0] [1.1920929e-07]

