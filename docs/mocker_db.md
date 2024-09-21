```python
from mocker_db import MockerDB, MockerConnector, SentenceTransformerEmbedder
```

### 1. Inserting values into the database

MockerDB can be used as ephemeral database where everything is saved in memory, but also can be persisted in one file for the database and another for embeddings storage.

Embedder is set to sentence_transformer by default and processed locally, custom embedders that connect to an api or use other open source models could be used as long as they have the same interface. 


```python
# Initialization
handler = MockerDB(
    # optional
    embedder_params = {'model_name_or_path' : 'paraphrase-multilingual-mpnet-base-v2',
                        'processing_type' : 'batch',
                        'tbatch_size' : 500},
    use_embedder = True,
    embedder = SentenceTransformerEmbedder,
    persist = True
)
# Initialize empty database
handler.establish_connection(
    # optional for persist
    file_path = "./mock_persist",
    embs_file_path = "./mock_embs_persist",
)
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


### 2. Searching and retrieving values from the database

There are multiple options for search which could be used together or separately:

- simple filter
- filter with keywords
- llm filter
- search based on similarity

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

    [{'embedding': '[-4.94665056e-02 -2.38676026e-...', '&embedded_field': 'text...'}]


### 3. Removing values from the database


```python
print(f"Items in the database {len(handler.data)}")
handler.remove_from_database(filter_criteria = {"text": "Sample text 1"})
print(f"Items left in the database {len(handler.data)}")

```

    Items in the database 2
    Items left in the database 1


### 4 Embeding text


```python
results = handler.embed_texts(
    texts = [
    "Short. Variation 1: Short.",
    "Another medium-length example, aiming to test the variability in processing different lengths of text inputs. Variation 2: processing lengths medium-length example, in inputs. to variability aiming test of text different the Another"
  ]
)

print(str(results)[0:300] + "...")
```

    {'embeddings': [[0.04973424971103668, -0.43570247292518616, -0.014545125886797905, -0.03648979589343071, -0.04165348783135414, -0.04544278606772423, -0.07025150209665298, 0.10043243318796158, -0.20846229791641235, 0.15596869587898254, 0.11489829421043396, -0.13442179560661316, -0.02425091527402401, ...


### 5. Using MockerDB API

Remote Mocker can be used via very similar methods to the local one.


```python
# Initialization
handler = MockerDB(
    skip_post_init=True
)
# Initialize empty database
handler.establish_connection(
     # optional for connecting to api
    connection_details = {
        'base_url' : "http://localhost:8000/mocker-db"
    }
)
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
```

    HTTP Request: POST http://localhost:8000/mocker-db/insert "HTTP/1.1 200 OK"





    {'status': 'success', 'message': ''}



MockerAPI has multiple handlers stored in memory at a time, they can be displayed with number of items and memory estimate.


```python
handler.show_handlers()
```

    HTTP Request: GET http://localhost:8000/mocker-db/active_handlers "HTTP/1.1 200 OK"





    {'results': [{'handler': 'default',
       'items': 4,
       'memory_usage': 1.3744659423828125}],
     'status': 'success',
     'message': '',
     'handlers': ['default'],
     'items': [4],
     'memory_usage': [1.3744659423828125]}




```python
results = handler.search_database(
    query = "text",
    filter_criteria = {
        "text" : "Sample text 1",
    }
)

results
```

    HTTP Request: POST http://localhost:8000/mocker-db/search "HTTP/1.1 200 OK"





    {'status': 'success',
     'message': '',
     'handler': 'default',
     'results': [{'other_field': 'Additional data', 'text': 'Example text 1'},
      {'other_field': 'Additional data', 'text': 'Example text 2'},
      {'text': 'Sample text 1', 'text2': 'Sample text 1'},
      {'text': 'Sample text 2', 'text2': 'Sample text 2'}]}




```python
results = handler.embed_texts(
    texts = [
    "Short. Variation 1: Short.",
    "Another medium-length example, aiming to test the variability in processing different lengths of text inputs. Variation 2: processing lengths medium-length example, in inputs. to variability aiming test of text different the Another"
  ],
    # optional
    embedding_model = "intfloat/multilingual-e5-base"
)

print(str(results)[0:500] + "...")
```

    HTTP Request: POST http://localhost:8000/mocker-db/embed "HTTP/1.1 200 OK"


    {'status': 'success', 'message': '', 'handler': 'cache_mocker_intfloat_multilingual-e5-base', 'embedding_model': 'intfloat/multilingual-e5-base', 'embeddings': [[-0.021023565903306007, 0.03461984172463417, -0.01310338918119669, 0.03071131743490696, 0.023395607247948647, -0.04054545238614082, -0.015805143862962723, -0.02682858146727085, 0.01583343744277954, 0.01763748936355114, 0.0008703064522705972, -0.011133715510368347, 0.11296682059764862, 0.015158131718635559, -0.0466904453933239, -0.0481428...



```python
handler.show_handlers()
```

    HTTP Request: GET http://localhost:8000/mocker-db/active_handlers "HTTP/1.1 200 OK"





    {'results': [{'handler': 'default',
       'items': 4,
       'memory_usage': 1.3749237060546875},
      {'handler': 'cache_mocker_intfloat_multilingual-e5-base',
       'items': 2,
       'memory_usage': 1.3611679077148438}],
     'status': 'success',
     'message': '',
     'handlers': ['default', 'cache_mocker_intfloat_multilingual-e5-base'],
     'items': [4, 2],
     'memory_usage': [1.3749237060546875, 1.3611679077148438]}


