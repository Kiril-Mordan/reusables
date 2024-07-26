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

    /home/kyriosskia/miniconda3/envs/testenv/lib/python3.10/site-packages/tqdm/auto.py:21: TqdmWarning: IProgress not found. Please update jupyter and ipywidgets. See https://ipywidgets.readthedocs.io/en/stable/user_install.html
      from .autonotebook import tqdm as notebook_tqdm


## Usage examples

The examples contain:
1. Basic data insertion and retrieval
2. Text embedding and searching
3. Advanced filtering and removal
4. Testing the HNSW search algorithm
5. Simulating database connection and persistence


### 1. Basic Data Insertion and Retrieval


```python
# Initialization
handler = MockerDB(
    # optional
    embedder_params = {'model_name_or_path' : 'paraphrase-multilingual-mpnet-base-v2',
                        'processing_type' : 'batch',
                        'tbatch_size' : 500},
    embedder = SentenceTransformerEmbedder,
    ## optional/ for similarity search
    similarity_search_h = MockerSimilaritySearch,
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

    Items in the database 4


### Retrieve Data Basics


```python
# Retrieve Data
handler.filter_keys(subkey="text", subvalue="Sample text 1")
handler.search_database_keys(query='text')
results = handler.get_dict_results(return_keys_list=["text"])
distances = handler.results_dictances
print(results)
print(distances)
```

    [{'text': 'Sample text 1'}]
    [0.6744726]


### Search and retrieve data

- get all keys


```python
results = handler.search_database(
    query = "text",
    filter_criteria = {
        "text" : "Sample text 1",
    },
    return_keys_list=None
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

    [{'text': 'Sample text 1...', 'text2': 'Sample text 1...', 'embedding': '[-4.94665056e-02 -2.38676026e-...'}]


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

    [{'embedding': '[-4.94665056e-02 -2.38676026e-...'}]


### 2. Text Embedding and Searching


```python
ste = SentenceTransformerEmbedder(# optional / adaptor parameters
                                  processing_type = '',
                                  tbatch_size = 500,
                                  max_workers = 2,
                                  # sentence transformer parameters
                                  model_name_or_path = 'paraphrase-multilingual-mpnet-base-v2',)
```


```python
# Single Text Embedding
query = "Sample query"
embedded_query = ste.embed(query,
                           # optional
                           processing_type='')
print(embedded_query[0:50])
```

    [-0.04973587  0.09520266 -0.01219509  0.09253872 -0.02301828 -0.0272102
      0.05683957  0.09710974  0.10683873  0.05812286  0.13227554  0.01142828
     -0.06957257  0.06980742 -0.05259363 -0.05755996  0.00816178 -0.00836837
     -0.00861246  0.01442065  0.01188813 -0.09503674  0.07125735 -0.04827795
      0.01473159  0.01084172 -0.10482483  0.0701253  -0.0472064   0.10030049
      0.04455939  0.0213189   0.00667923 -0.0525919   0.06822997 -0.09520472
     -0.00581364 -0.02451883 -0.00384985  0.02750736  0.06960268  0.24013738
     -0.01220023  0.05890927 -0.08468661  0.11379698 -0.03594772 -0.05652961
     -0.01621804  0.09546741]



```python
# Batch Text Embedding
queries = ["Sample query", "Sample query 2"]
embedded_query = ste.embed(queries,
                           # optional
                           processing_type='batch')
print(embedded_query[0][0:50])
print("---")
print(embedded_query[1][0:50])
```

    [-0.04973588  0.09520268 -0.01219508  0.09253875 -0.02301828 -0.02721018
      0.05683955  0.09710979  0.10683873  0.05812287  0.13227554  0.01142833
     -0.06957259  0.06980736 -0.05259363 -0.05755996  0.0081618  -0.00836839
     -0.00861242  0.01442068  0.01188811 -0.09503674  0.07125735 -0.04827797
      0.01473157  0.01084175 -0.10482486  0.07012529 -0.04720639  0.10030051
      0.04455936  0.02131891  0.00667919 -0.05259192  0.06822997 -0.09520471
     -0.00581361 -0.02451885 -0.00384985  0.02750732  0.06960279  0.24013741
     -0.0122002   0.05890926 -0.08468664  0.11379691 -0.03594773 -0.05652963
     -0.01621806  0.09546743]
    ---
    [-0.05087035  0.12317687 -0.0139253   0.10524721 -0.07614311 -0.02349636
      0.05829769  0.15128353  0.181198    0.03745941  0.12174654  0.00639845
     -0.04045051  0.12758298 -0.06155458 -0.0673613   0.04713941 -0.04134275
     -0.12165944  0.04409872  0.01834138 -0.04796622  0.04922184 -0.00641214
      0.01420629 -0.03602948 -0.01026758  0.09232265 -0.04927171  0.0398545
      0.03566905  0.08338926  0.04922605 -0.09951876  0.05138123 -0.13344647
      0.01626777 -0.01189728  0.00599212  0.05663404  0.04282088  0.26432776
     -0.01122816  0.07177623 -0.11822147  0.08731955 -0.04965367  0.03697514
      0.08965278  0.03107026]



```python
# Search Database
search_results = handler.search_database(query, return_keys_list=["text"])

# Display Results
print(search_results)

```

    [{'text': 'Sample text 1'}, {'text': 'Sample text 2'}, {'text': 'Sample text 2'}]


### 3. Advanced Filtering and Removal


```python
# Advanced Filtering
filter_criteria = {"text": "Sample text 1"}
handler.filter_database(filter_criteria)
filtered_data = handler.filtered_data
print(f"Filtered data {len(filtered_data)}")

# Data Removal
handler.remove_from_database(filter_criteria)
print(f"Items left in the database {len(handler.data)}")

```

    Filtered data 1
    Items left in the database 3


### 4. Testing the HNSW Search Algorithm


```python
mss = MockerSimilaritySearch(
    # optional
    search_results_n = 3,
    similarity_params = {'space':'cosine'},
    similarity_search_type ='linear'
)
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


### 5. Simulating Database Connection and Persistence


```python
# Establish Connection
handler.establish_connection()

# Change and Persist Data
handler.insert_values([{"text": "New sample text"}], "text")
handler.save_data()

# Reload Data
handler.establish_connection()
print(f"Items in the database {len(handler.data)}")

```

    Items in the database 3

