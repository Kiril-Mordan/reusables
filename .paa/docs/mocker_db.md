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
    similarity_search_type = 'linear_torch',
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
sentences = [
    "The cat slept.",
    "It rained today.",
    "She smiled gently.",
    "Books hold knowledge.",
    "The sun set behind the mountains, casting a golden glow over the valley.",
    "He quickly realized that time was slipping away, and he needed to act fast.",
    "The concert was an unforgettable experience, filled with laughter and joy.",
    "Despite the challenges, they managed to build a beautiful home together.",
    "As the wind howled through the ancient trees, scattering leaves and whispering secrets of the forest, she stood there, gazing up at the endless expanse of stars, feeling both infinitely small and profoundly connected to the universe.",
    "While the project seemed daunting at first, requiring countless hours of research, planning, and execution, the team worked tirelessly, motivated by their shared goal of creating something truly remarkable and innovative in their field.",
    "In the bustling city streets, amidst the constant hum of traffic and chatter, he found himself contemplating life's mysteries, pondering the choices that had brought him to this very moment and wondering where the path ahead would lead.",
    "The conference was a gathering of minds from around the globe, each participant bringing their unique perspectives and insights to the table, fostering a vibrant exchange of ideas that would shape the future of their respective fields for years to come."
]

# Insert Data
values_list = [
    {'text' : t, 'n_words' : len(t.split())} for t in sentences
]
handler.insert_values(values_list, "text")
print(f"Items in the database {len(handler.data)}")
```

    Items in the database 14


### 2. Searching and retrieving values from the database

There are multiple options for search which could be used together or separately:

- simple filter
- filter with keywords
- llm filter
- search based on similarity

#### get all keys


```python
results = handler.search_database(
    query = "cat",
    filter_criteria = {
        "n_words" : 3,
    }
)
print([{k: str(v)[:30] + "..." for k, v in result.items()} for result in results])
```

    [{'text': 'The cat slept....', 'n_words': '3...'}, {'text': 'She smiled gently....', 'n_words': '3...'}, {'text': 'It rained today....', 'n_words': '3...'}, {'text': 'Books hold knowledge....', 'n_words': '3...'}]


#### get all keys with keywords search


```python
results = handler.search_database(
    # when keyword key is provided filter is used to pass keywords
    filter_criteria = {
        "text" : ["sun"],
    },
    keyword_check_keys = ['text'],
    # percentage of filter keyword allowed to be different
    keyword_check_cutoff = 1,
    return_keys_list=['text']
)
print([{k: str(v)[:30] + "..." for k, v in result.items()} for result in results])
```

    [{'text': 'The sun set behind the mountai...'}]


#### get all key - n_words


```python
results = handler.search_database(
    query = "cat",
    filter_criteria = {
        "n_words" : 3,
    },
    return_keys_list=["-n_words"])
print([{k: str(v)[:30] + "..." for k, v in result.items()} for result in results])
```

    [{'text': 'The cat slept....'}, {'text': 'She smiled gently....'}, {'text': 'It rained today....'}, {'text': 'Books hold knowledge....'}]


#### get all keys + distance


```python
results = handler.search_database(
    query = "cat slept",
    filter_criteria = {
        "n_words" : 3,
    },
    return_keys_list=["+&distance"]
)
print([{k: str(v)[:30] + "..." for k, v in result.items()} for result in results])
```

    [{'text': 'The cat slept....', 'n_words': '3...', '&distance': '0.9757655658500587...'}, {'text': 'She smiled gently....', 'n_words': '3...', '&distance': '0.255370996400475...'}, {'text': 'It rained today....', 'n_words': '3...', '&distance': '0.049663160920329866...'}, {'text': 'Books hold knowledge....', 'n_words': '3...', '&distance': '0.011214848789777708...'}]


#### get distance


```python
results = handler.search_database(
    query = "cat slept",
    filter_criteria = {
        "n_words" : 3,
    },
    return_keys_list=["&distance"]
)
print([{k: str(v)[:30] + "..." for k, v in result.items()} for result in results])
```

    [{'&distance': '0.9757655658500587...'}, {'&distance': '0.255370996400475...'}, {'&distance': '0.049663160920329866...'}, {'&distance': '0.011214848789777708...'}]


#### get all keys + embeddings


```python
results = handler.search_database(
    query = "cat slept",
    filter_criteria = {
        "n_words" : 3,
    },
    return_keys_list=["+embedding"]
)
print([{k: str(v)[:30] + "..." for k, v in result.items()} for result in results])
```

    [{'text': 'The cat slept....', 'n_words': '3...', 'embedding': '[-3.86438631e-02  1.23167999e-...'}, {'text': 'She smiled gently....', 'n_words': '3...', 'embedding': '[-2.46711988e-02  2.37020120e-...'}, {'text': 'It rained today....', 'n_words': '3...', 'embedding': '[-1.35887757e-01 -2.52719939e-...'}, {'text': 'Books hold knowledge....', 'n_words': '3...', 'embedding': '[ 6.20862879e-02  1.13785893e-...'}]


#### get embeddings


```python
results = handler.search_database(
    query = "cat slept",
    filter_criteria = {
        "n_words" : 3,
    },
    return_keys_list=["embedding"]
)
print([{k: str(v)[:30] + "..." for k, v in result.items()} for result in results])

```

    [{'embedding': '[-3.86438631e-02  1.23167999e-...'}, {'embedding': '[-2.46711988e-02  2.37020120e-...'}, {'embedding': '[-1.35887757e-01 -2.52719939e-...'}, {'embedding': '[ 6.20862879e-02  1.13785893e-...'}]


#### get embeddings and embedded field


```python
results = handler.search_database(
    query = "cat slept",
    filter_criteria = {
        "n_words" : 3,
    },
    return_keys_list=["embedding", "+&embedded_field"]
)
print([{k: str(v)[:30] + "..." for k, v in result.items()} for result in results])

```

    [{'&embedded_field': 'text...', 'embedding': '[-3.86438631e-02  1.23167999e-...'}, {'&embedded_field': 'text...', 'embedding': '[-2.46711988e-02  2.37020120e-...'}, {'&embedded_field': 'text...', 'embedding': '[-1.35887757e-01 -2.52719939e-...'}, {'&embedded_field': 'text...', 'embedding': '[ 6.20862879e-02  1.13785893e-...'}]


#### get all keys with llm search


```python
# Initialization
handler = MockerDB(
    # optional
    persist = True,
    llm_filter_params = {
        "connection_string" : "http://127.0.0.1:8000/proompter/prompt_chat"
    }
)
# Initialize empty database
handler.establish_connection(
    # optional for persist
    file_path = "./mock_persist",
    embs_file_path = "./mock_embs_persist",
)

results = await handler.search_database_async(
    llm_search_keys=['text'],
    filter_criteria = {
        "text" : ["cat"],
    }
)
print([{k: str(v)[:30] + "..." for k, v in result.items()} for result in results])
```

    [{'text': 'The cat slept....', 'n_words': '3...'}]


### 3. Removing values from the database


```python
print(f"Items in the database {len(handler.data)}")
handler.remove_from_database(filter_criteria = {"n_words" : 11})
print(f"Items left in the database {len(handler.data)}")

```

    Items in the database 12
    Items left in the database 10


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
sentences = [
    "The cat slept.",
    "It rained today.",
    "She smiled gently.",
    "Books hold knowledge.",
    "The sun set behind the mountains, casting a golden glow over the valley.",
    "He quickly realized that time was slipping away, and he needed to act fast.",
    "The concert was an unforgettable experience, filled with laughter and joy.",
    "Despite the challenges, they managed to build a beautiful home together.",
    "As the wind howled through the ancient trees, scattering leaves and whispering secrets of the forest, she stood there, gazing up at the endless expanse of stars, feeling both infinitely small and profoundly connected to the universe.",
    "While the project seemed daunting at first, requiring countless hours of research, planning, and execution, the team worked tirelessly, motivated by their shared goal of creating something truly remarkable and innovative in their field.",
    "In the bustling city streets, amidst the constant hum of traffic and chatter, he found himself contemplating life's mysteries, pondering the choices that had brought him to this very moment and wondering where the path ahead would lead.",
    "The conference was a gathering of minds from around the globe, each participant bringing their unique perspectives and insights to the table, fostering a vibrant exchange of ideas that would shape the future of their respective fields for years to come."
]

# Insert Data
values_list = [
    {'text' : t, 'n_words' : len(t.split())} for t in sentences
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
       'items': 14,
       'memory_usage': 1.4558258056640625}],
     'status': 'success',
     'message': '',
     'handlers': ['default'],
     'items': [14],
     'memory_usage': [1.4558258056640625]}




```python
results = handler.search_database(
    query = "cat",
    filter_criteria = {
        "n_words" : 3,
    }
)

results
```

    HTTP Request: POST http://localhost:8000/mocker-db/search "HTTP/1.1 200 OK"





    {'status': 'success',
     'message': '',
     'handler': 'default',
     'results': [{'text': 'The cat slept.', 'n_words': 3},
      {'text': 'Books hold knowledge.', 'n_words': 3},
      {'text': 'It rained today.', 'n_words': 3},
      {'text': 'She smiled gently.', 'n_words': 3}]}




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
       'items': 14,
       'memory_usage': 1.4564743041992188},
      {'handler': 'cache_mocker_intfloat_multilingual-e5-base',
       'items': 2,
       'memory_usage': 1.3639755249023438}],
     'status': 'success',
     'message': '',
     'handlers': ['default', 'cache_mocker_intfloat_multilingual-e5-base'],
     'items': [14, 2],
     'memory_usage': [1.4564743041992188, 1.3639755249023438]}


