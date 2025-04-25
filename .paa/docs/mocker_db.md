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

    Items in the database 12


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

    [{'text': 'The cat slept....', 'n_words': '3...', '&distance': '0.9757655893784214...'}, {'text': 'She smiled gently....', 'n_words': '3...', '&distance': '0.25537100167603033...'}, {'text': 'It rained today....', 'n_words': '3...', '&distance': '0.049663180663929454...'}, {'text': 'Books hold knowledge....', 'n_words': '3...', '&distance': '0.011214834039176086...'}]


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

    [{'&distance': '0.9757655893784214...'}, {'&distance': '0.25537100167603033...'}, {'&distance': '0.049663180663929454...'}, {'&distance': '0.011214834039176086...'}]


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

    [{'text': 'The cat slept....', 'n_words': '3...', 'embedding': '[-3.86438444e-02  1.23167984e-...'}, {'text': 'She smiled gently....', 'n_words': '3...', 'embedding': '[-2.46711876e-02  2.37020180e-...'}, {'text': 'It rained today....', 'n_words': '3...', 'embedding': '[-1.35887727e-01 -2.52719879e-...'}, {'text': 'Books hold knowledge....', 'n_words': '3...', 'embedding': '[ 6.20863438e-02  1.13785945e-...'}]


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

    [{'embedding': '[-3.86438444e-02  1.23167984e-...'}, {'embedding': '[-2.46711876e-02  2.37020180e-...'}, {'embedding': '[-1.35887727e-01 -2.52719879e-...'}, {'embedding': '[ 6.20863438e-02  1.13785945e-...'}]


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

    [{'embedding': '[-3.86438444e-02  1.23167984e-...', '&embedded_field': 'text...'}, {'embedding': '[-2.46711876e-02  2.37020180e-...', '&embedded_field': 'text...'}, {'embedding': '[-1.35887727e-01 -2.52719879e-...', '&embedded_field': 'text...'}, {'embedding': '[ 6.20863438e-02  1.13785945e-...', '&embedded_field': 'text...'}]


#### get all keys with llm search

Ollama


```python
import logging
logging.disable(logging.INFO)

# Initialization
handler = MockerDB(
    # optional
    persist = True,
    llm_conn_params = {

        'llm_h_type' : 'OllamaConn',
        'llm_h_params' : {
            'connection_string' : 'http://127.0.0.1:11434',
            'model_name' : 'llama3.1:latest'
        }

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
        "text" : ["cat", "nature"],
    },
    return_keys_list=["+&cats"],
    ignore_cats_cache=False
)
print([{k: str(v)[:30] + "..." for k, v in result.items()} for result in results])
```

    [{'text': 'The cat slept....', 'n_words': '3...', '&cats': "{'text': ['cat']}..."}, {'text': 'The sun set behind the mountai...', 'n_words': '13...', '&cats': "{'text': ['nature']}..."}, {'text': 'As the wind howled through the...', 'n_words': '37...', '&cats': "{'text': ['nature']}..."}]



```python
handler.cats
```




    {'The cat slept.': {1: ['cat'], 0: ['nature']},
     'It rained today.': {1: [], 0: ['cat', 'nature']},
     'She smiled gently.': {1: [], 0: ['cat', 'nature']},
     'Books hold knowledge.': {1: [], 0: ['cat', 'nature']},
     'The sun set behind the mountains, casting a golden glow over the valley.': {1: ['nature'],
      0: ['cat']},
     'He quickly realized that time was slipping away, and he needed to act fast.': {1: [],
      0: ['cat', 'nature']},
     'The concert was an unforgettable experience, filled with laughter and joy.': {1: [],
      0: ['cat', 'nature']},
     'Despite the challenges, they managed to build a beautiful home together.': {1: [],
      0: ['cat', 'nature']},
     'As the wind howled through the ancient trees, scattering leaves and whispering secrets of the forest, she stood there, gazing up at the endless expanse of stars, feeling both infinitely small and profoundly connected to the universe.': {1: ['nature'],
      0: ['cat']},
     'While the project seemed daunting at first, requiring countless hours of research, planning, and execution, the team worked tirelessly, motivated by their shared goal of creating something truly remarkable and innovative in their field.': {1: [],
      0: ['cat', 'nature']},
     "In the bustling city streets, amidst the constant hum of traffic and chatter, he found himself contemplating life's mysteries, pondering the choices that had brought him to this very moment and wondering where the path ahead would lead.": {1: [],
      0: ['cat', 'nature']},
     'The conference was a gathering of minds from around the globe, each participant bringing their unique perspectives and insights to the table, fostering a vibrant exchange of ideas that would shape the future of their respective fields for years to come.': {1: [],
      0: ['cat', 'nature']}}



OpenAI


```python
import logging
logging.disable(logging.INFO)

from dotenv import load_dotenv
import os

load_dotenv("../../credentials")

# Initialization
handler = MockerDB(
    # optional
    persist = True,
    llm_conn_params = {

        'llm_h_type' : 'OpenAIConn',
        'llm_h_params' : {
            'model_name' : 'gpt-4o-mini',
            'env_mapping' : {
                'api_key' : "OPENAI_KEY"
            }
        }

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
        "text" : ["cat", "nature"],
    }
)
print([{k: str(v)[:30] + "..." for k, v in result.items()} for result in results])
```

    [{'text': 'The cat slept....', 'n_words': '3...'}, {'text': 'The sun set behind the mountai...', 'n_words': '13...'}, {'text': 'As the wind howled through the...', 'n_words': '37...'}]


### 3. Removing values from the database


```python
print(f"Items in the database {len(handler.data)}")
handler.remove_from_database(filter_criteria = {"n_words" : 11})
print(f"Items left in the database {len(handler.data)}")

```

    Items in the database 14
    Items left in the database 12


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




    {'status': 'success', 'message': ''}



MockerAPI has multiple handlers stored in memory at a time, they can be displayed with number of items and memory estimate.


```python
handler.show_handlers()
```




    {'results': [{'handler': 'default',
       'items': 12,
       'memory_usage': 1.4748001098632812}],
     'status': 'success',
     'message': '',
     'handlers': ['default'],
     'items': [12],
     'memory_usage': [1.4748001098632812]}




```python
results = handler.search_database(
    query = "cat",
    filter_criteria = {
        "n_words" : 3,
    }
)

results
```




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

    {'status': 'success', 'message': '', 'handler': 'cache_mocker_intfloat_multilingual-e5-base', 'embedding_model': 'intfloat/multilingual-e5-base', 'embeddings': [[-0.021023569628596306, 0.03461984172463417, -0.013103404082357883, 0.030711326748132706, 0.023395603522658348, -0.040545400232076645, -0.01580517739057541, -0.026828577741980553, 0.015833470970392227, 0.017637528479099274, 0.0008703444618731737, -0.011133708991110325, 0.11296682059764862, 0.015158110298216343, -0.04669041559100151, -0.0...



```python
handler.show_handlers()
```




    {'results': [{'handler': 'default',
       'items': 12,
       'memory_usage': 1.4762191772460938},
      {'handler': 'cache_mocker_intfloat_multilingual-e5-base',
       'items': 2,
       'memory_usage': 1.4075469970703125}],
     'status': 'success',
     'message': '',
     'handlers': ['default', 'cache_mocker_intfloat_multilingual-e5-base'],
     'items': [12, 2],
     'memory_usage': [1.4762191772460938, 1.4075469970703125]}


