# Comparison Frame

Utility designed to automate and streamline the process of comparing textual data with a use of various metrics
such as character and word count, punctuation usage, and semantic similarity. Allow to not only compare results but also store validation data and test statuses.



```python
import sys
sys.path.append('../')
from python_modules.comparisonframe import ComparisonFrame
```

## Usage examples

The examples contain: 
1. creating validation set and saving it to be reused
2. comparing newly generated data with expected results 
3. recording test statuses
4. reseting statuses, flushing records and comparison results

### 1. Creating validation set

### 1.1 Initialize comparison class


```python
comparer = ComparisonFrame(
    # optionally 
    ## provide name of the model from sentence_transformer package
    model_name = "all-mpnet-base-v2",
    ## provide filenames to persist state
    record_file = "record_file.csv",  # file where queries and expected results are stored
    results_file = "comparison_results.csv", # file where comparison results will be stored
    embeddings_file = "embeddings.dill",
    ## provide soup for scraping if was already defined externally
    embedder = None
)
```

    INFO:sentence_transformers.SentenceTransformer:Load pretrained SentenceTransformer: all-mpnet-base-v2
    DEBUG:urllib3.connectionpool:Starting new HTTPS connection (1): huggingface.co:443
    DEBUG:urllib3.connectionpool:https://huggingface.co:443 "GET /api/models/sentence-transformers/all-mpnet-base-v2 HTTP/1.1" 200 11716
    DEBUG:urllib3.connectionpool:https://huggingface.co:443 "HEAD /sentence-transformers/all-mpnet-base-v2/resolve/5681fe04da6e48e851d5dd1af673670cdb299753/.gitattributes HTTP/1.1" 200 0
    DEBUG:filelock:Attempting to acquire lock 139909127738560 on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/.gitattributes.lock
    DEBUG:filelock:Lock 139909127738560 acquired on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/.gitattributes.lock
    DEBUG:urllib3.connectionpool:https://huggingface.co:443 "GET /sentence-transformers/all-mpnet-base-v2/resolve/5681fe04da6e48e851d5dd1af673670cdb299753/.gitattributes HTTP/1.1" 200 1175



    Downloading (…)99753/.gitattributes:   0%|          | 0.00/1.18k [00:00<?, ?B/s]


    DEBUG:filelock:Attempting to release lock 139909127738560 on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/.gitattributes.lock
    DEBUG:filelock:Lock 139909127738560 released on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/.gitattributes.lock
    DEBUG:urllib3.connectionpool:https://huggingface.co:443 "HEAD /sentence-transformers/all-mpnet-base-v2/resolve/5681fe04da6e48e851d5dd1af673670cdb299753/1_Pooling/config.json HTTP/1.1" 200 0
    DEBUG:filelock:Attempting to acquire lock 139905264131520 on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/1_Pooling/config.json.lock
    DEBUG:filelock:Lock 139905264131520 acquired on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/1_Pooling/config.json.lock
    DEBUG:urllib3.connectionpool:https://huggingface.co:443 "GET /sentence-transformers/all-mpnet-base-v2/resolve/5681fe04da6e48e851d5dd1af673670cdb299753/1_Pooling/config.json HTTP/1.1" 200 190



    Downloading (…)_Pooling/config.json:   0%|          | 0.00/190 [00:00<?, ?B/s]


    DEBUG:filelock:Attempting to release lock 139905264131520 on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/1_Pooling/config.json.lock
    DEBUG:filelock:Lock 139905264131520 released on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/1_Pooling/config.json.lock
    DEBUG:urllib3.connectionpool:https://huggingface.co:443 "HEAD /sentence-transformers/all-mpnet-base-v2/resolve/5681fe04da6e48e851d5dd1af673670cdb299753/README.md HTTP/1.1" 200 0
    DEBUG:filelock:Attempting to acquire lock 139905264131520 on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/README.md.lock
    DEBUG:filelock:Lock 139905264131520 acquired on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/README.md.lock
    DEBUG:urllib3.connectionpool:https://huggingface.co:443 "GET /sentence-transformers/all-mpnet-base-v2/resolve/5681fe04da6e48e851d5dd1af673670cdb299753/README.md HTTP/1.1" 200 10571



    Downloading (…)0cdb299753/README.md:   0%|          | 0.00/10.6k [00:00<?, ?B/s]


    DEBUG:filelock:Attempting to release lock 139905264131520 on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/README.md.lock
    DEBUG:filelock:Lock 139905264131520 released on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/README.md.lock
    DEBUG:urllib3.connectionpool:https://huggingface.co:443 "HEAD /sentence-transformers/all-mpnet-base-v2/resolve/5681fe04da6e48e851d5dd1af673670cdb299753/config.json HTTP/1.1" 200 0
    DEBUG:filelock:Attempting to acquire lock 139905264131520 on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/config.json.lock
    DEBUG:filelock:Lock 139905264131520 acquired on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/config.json.lock
    DEBUG:urllib3.connectionpool:https://huggingface.co:443 "GET /sentence-transformers/all-mpnet-base-v2/resolve/5681fe04da6e48e851d5dd1af673670cdb299753/config.json HTTP/1.1" 200 571



    Downloading (…)db299753/config.json:   0%|          | 0.00/571 [00:00<?, ?B/s]


    DEBUG:filelock:Attempting to release lock 139905264131520 on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/config.json.lock
    DEBUG:filelock:Lock 139905264131520 released on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/config.json.lock
    DEBUG:urllib3.connectionpool:https://huggingface.co:443 "HEAD /sentence-transformers/all-mpnet-base-v2/resolve/5681fe04da6e48e851d5dd1af673670cdb299753/config_sentence_transformers.json HTTP/1.1" 200 0
    DEBUG:filelock:Attempting to acquire lock 139905264131520 on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/config_sentence_transformers.json.lock
    DEBUG:filelock:Lock 139905264131520 acquired on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/config_sentence_transformers.json.lock
    DEBUG:urllib3.connectionpool:https://huggingface.co:443 "GET /sentence-transformers/all-mpnet-base-v2/resolve/5681fe04da6e48e851d5dd1af673670cdb299753/config_sentence_transformers.json HTTP/1.1" 200 116



    Downloading (…)ce_transformers.json:   0%|          | 0.00/116 [00:00<?, ?B/s]


    DEBUG:filelock:Attempting to release lock 139905264131520 on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/config_sentence_transformers.json.lock
    DEBUG:filelock:Lock 139905264131520 released on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/config_sentence_transformers.json.lock
    DEBUG:urllib3.connectionpool:https://huggingface.co:443 "HEAD /sentence-transformers/all-mpnet-base-v2/resolve/5681fe04da6e48e851d5dd1af673670cdb299753/data_config.json HTTP/1.1" 200 0
    DEBUG:filelock:Attempting to acquire lock 139905264131376 on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/data_config.json.lock
    DEBUG:filelock:Lock 139905264131376 acquired on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/data_config.json.lock
    DEBUG:urllib3.connectionpool:https://huggingface.co:443 "GET /sentence-transformers/all-mpnet-base-v2/resolve/5681fe04da6e48e851d5dd1af673670cdb299753/data_config.json HTTP/1.1" 200 39265



    Downloading (…)753/data_config.json:   0%|          | 0.00/39.3k [00:00<?, ?B/s]


    DEBUG:filelock:Attempting to release lock 139905264131376 on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/data_config.json.lock
    DEBUG:filelock:Lock 139905264131376 released on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/data_config.json.lock
    DEBUG:urllib3.connectionpool:https://huggingface.co:443 "HEAD /sentence-transformers/all-mpnet-base-v2/resolve/5681fe04da6e48e851d5dd1af673670cdb299753/pytorch_model.bin HTTP/1.1" 302 0
    DEBUG:filelock:Attempting to acquire lock 139905263603280 on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/pytorch_model.bin.lock
    DEBUG:filelock:Lock 139905263603280 acquired on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/pytorch_model.bin.lock
    DEBUG:urllib3.connectionpool:Starting new HTTPS connection (1): cdn-lfs.huggingface.co:443
    DEBUG:urllib3.connectionpool:https://cdn-lfs.huggingface.co:443 "GET /sentence-transformers/all-mpnet-base-v2/a8fd120b1a0032e70ff3d4b8ab8e46a6d01c2cb08ffe7c007a021c1788928146?response-content-disposition=attachment%3B+filename*%3DUTF-8%27%27pytorch_model.bin%3B+filename%3D%22pytorch_model.bin%22%3B&response-content-type=application%2Foctet-stream&Expires=1699490577&Policy=eyJTdGF0ZW1lbnQiOlt7IkNvbmRpdGlvbiI6eyJEYXRlTGVzc1RoYW4iOnsiQVdTOkVwb2NoVGltZSI6MTY5OTQ5MDU3N319LCJSZXNvdXJjZSI6Imh0dHBzOi8vY2RuLWxmcy5odWdnaW5nZmFjZS5jby9zZW50ZW5jZS10cmFuc2Zvcm1lcnMvYWxsLW1wbmV0LWJhc2UtdjIvYThmZDEyMGIxYTAwMzJlNzBmZjNkNGI4YWI4ZTQ2YTZkMDFjMmNiMDhmZmU3YzAwN2EwMjFjMTc4ODkyODE0Nj9yZXNwb25zZS1jb250ZW50LWRpc3Bvc2l0aW9uPSomcmVzcG9uc2UtY29udGVudC10eXBlPSoifV19&Signature=ZKzLlVqdeNjcsewJUYy8RAcQnyFhYXYHk6yaEER4ywZKePPwMYzSduEzxn5UDw1aD2QAtcSyL9CxtpLHTEpxq2yJ2lWkqC4XNAvJLrtWJ1iwuy0SpdFwcVCjbaVk0-7dzg8tXcXzweoL8GIF6LImUWmB4Zybe1kvvVJHAvWnHebLLlubxEhxez~BxGf9~GdnCuUXbmvAoZfABGFk2YsqV7b3jhaAneHMbeG5~MMCmxAL3h1h~QHjE0ytR5wc4WyfM79iKYNukj3M68oh3XdBN-FJ5yiL37hlxMuSakmmJhDCuBestjLcW6WpxcgZ3erBxaajxvu6FHh1PE3VoSw4vw__&Key-Pair-Id=KVTP0A1DKRTAX HTTP/1.1" 200 438011953



    Downloading pytorch_model.bin:   0%|          | 0.00/438M [00:00<?, ?B/s]


    DEBUG:filelock:Attempting to release lock 139905263603280 on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/pytorch_model.bin.lock
    DEBUG:filelock:Lock 139905263603280 released on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/pytorch_model.bin.lock
    DEBUG:urllib3.connectionpool:https://huggingface.co:443 "HEAD /sentence-transformers/all-mpnet-base-v2/resolve/5681fe04da6e48e851d5dd1af673670cdb299753/sentence_bert_config.json HTTP/1.1" 200 0
    DEBUG:filelock:Attempting to acquire lock 139905264131520 on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/sentence_bert_config.json.lock
    DEBUG:filelock:Lock 139905264131520 acquired on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/sentence_bert_config.json.lock
    DEBUG:urllib3.connectionpool:https://huggingface.co:443 "GET /sentence-transformers/all-mpnet-base-v2/resolve/5681fe04da6e48e851d5dd1af673670cdb299753/sentence_bert_config.json HTTP/1.1" 200 53



    Downloading (…)nce_bert_config.json:   0%|          | 0.00/53.0 [00:00<?, ?B/s]


    DEBUG:filelock:Attempting to release lock 139905264131520 on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/sentence_bert_config.json.lock
    DEBUG:filelock:Lock 139905264131520 released on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/sentence_bert_config.json.lock
    DEBUG:urllib3.connectionpool:https://huggingface.co:443 "HEAD /sentence-transformers/all-mpnet-base-v2/resolve/5681fe04da6e48e851d5dd1af673670cdb299753/special_tokens_map.json HTTP/1.1" 200 0
    DEBUG:filelock:Attempting to acquire lock 139905263725728 on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/special_tokens_map.json.lock
    DEBUG:filelock:Lock 139905263725728 acquired on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/special_tokens_map.json.lock
    DEBUG:urllib3.connectionpool:https://huggingface.co:443 "GET /sentence-transformers/all-mpnet-base-v2/resolve/5681fe04da6e48e851d5dd1af673670cdb299753/special_tokens_map.json HTTP/1.1" 200 239



    Downloading (…)cial_tokens_map.json:   0%|          | 0.00/239 [00:00<?, ?B/s]


    DEBUG:filelock:Attempting to release lock 139905263725728 on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/special_tokens_map.json.lock
    DEBUG:filelock:Lock 139905263725728 released on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/special_tokens_map.json.lock
    DEBUG:urllib3.connectionpool:https://huggingface.co:443 "HEAD /sentence-transformers/all-mpnet-base-v2/resolve/5681fe04da6e48e851d5dd1af673670cdb299753/tokenizer.json HTTP/1.1" 200 0
    DEBUG:filelock:Attempting to acquire lock 139905263723856 on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/tokenizer.json.lock
    DEBUG:filelock:Lock 139905263723856 acquired on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/tokenizer.json.lock
    DEBUG:urllib3.connectionpool:https://huggingface.co:443 "GET /sentence-transformers/all-mpnet-base-v2/resolve/5681fe04da6e48e851d5dd1af673670cdb299753/tokenizer.json HTTP/1.1" 200 466021



    Downloading (…)99753/tokenizer.json:   0%|          | 0.00/466k [00:00<?, ?B/s]


    DEBUG:filelock:Attempting to release lock 139905263723856 on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/tokenizer.json.lock
    DEBUG:filelock:Lock 139905263723856 released on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/tokenizer.json.lock
    DEBUG:urllib3.connectionpool:https://huggingface.co:443 "HEAD /sentence-transformers/all-mpnet-base-v2/resolve/5681fe04da6e48e851d5dd1af673670cdb299753/tokenizer_config.json HTTP/1.1" 200 0
    DEBUG:filelock:Attempting to acquire lock 139905264131520 on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/tokenizer_config.json.lock
    DEBUG:filelock:Lock 139905264131520 acquired on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/tokenizer_config.json.lock
    DEBUG:urllib3.connectionpool:https://huggingface.co:443 "GET /sentence-transformers/all-mpnet-base-v2/resolve/5681fe04da6e48e851d5dd1af673670cdb299753/tokenizer_config.json HTTP/1.1" 200 363



    Downloading (…)okenizer_config.json:   0%|          | 0.00/363 [00:00<?, ?B/s]


    DEBUG:filelock:Attempting to release lock 139905264131520 on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/tokenizer_config.json.lock
    DEBUG:filelock:Lock 139905264131520 released on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/tokenizer_config.json.lock
    DEBUG:urllib3.connectionpool:https://huggingface.co:443 "HEAD /sentence-transformers/all-mpnet-base-v2/resolve/5681fe04da6e48e851d5dd1af673670cdb299753/train_script.py HTTP/1.1" 200 0
    DEBUG:filelock:Attempting to acquire lock 139905263725728 on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/train_script.py.lock
    DEBUG:filelock:Lock 139905263725728 acquired on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/train_script.py.lock
    DEBUG:urllib3.connectionpool:https://huggingface.co:443 "GET /sentence-transformers/all-mpnet-base-v2/resolve/5681fe04da6e48e851d5dd1af673670cdb299753/train_script.py HTTP/1.1" 200 13123



    Downloading (…)9753/train_script.py:   0%|          | 0.00/13.1k [00:00<?, ?B/s]


    DEBUG:filelock:Attempting to release lock 139905263725728 on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/train_script.py.lock
    DEBUG:filelock:Lock 139905263725728 released on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/train_script.py.lock
    DEBUG:urllib3.connectionpool:https://huggingface.co:443 "HEAD /sentence-transformers/all-mpnet-base-v2/resolve/5681fe04da6e48e851d5dd1af673670cdb299753/vocab.txt HTTP/1.1" 200 0
    DEBUG:filelock:Attempting to acquire lock 139905263936800 on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/vocab.txt.lock
    DEBUG:filelock:Lock 139905263936800 acquired on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/vocab.txt.lock
    DEBUG:urllib3.connectionpool:https://huggingface.co:443 "GET /sentence-transformers/all-mpnet-base-v2/resolve/5681fe04da6e48e851d5dd1af673670cdb299753/vocab.txt HTTP/1.1" 200 231536



    Downloading (…)0cdb299753/vocab.txt:   0%|          | 0.00/232k [00:00<?, ?B/s]


    DEBUG:filelock:Attempting to release lock 139905263936800 on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/vocab.txt.lock
    DEBUG:filelock:Lock 139905263936800 released on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/vocab.txt.lock
    DEBUG:urllib3.connectionpool:https://huggingface.co:443 "HEAD /sentence-transformers/all-mpnet-base-v2/resolve/5681fe04da6e48e851d5dd1af673670cdb299753/modules.json HTTP/1.1" 200 0
    DEBUG:filelock:Attempting to acquire lock 139905264131520 on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/modules.json.lock
    DEBUG:filelock:Lock 139905264131520 acquired on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/modules.json.lock
    DEBUG:urllib3.connectionpool:https://huggingface.co:443 "GET /sentence-transformers/all-mpnet-base-v2/resolve/5681fe04da6e48e851d5dd1af673670cdb299753/modules.json HTTP/1.1" 200 349



    Downloading (…)b299753/modules.json:   0%|          | 0.00/349 [00:00<?, ?B/s]


    DEBUG:filelock:Attempting to release lock 139905264131520 on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/modules.json.lock
    DEBUG:filelock:Lock 139905264131520 released on /home/runner/.cache/torch/sentence_transformers/sentence-transformers_all-mpnet-base-v2/modules.json.lock
    INFO:sentence_transformers.SentenceTransformer:Use pytorch device: cpu


#### 1.2 Recording queries and expected responses (validation set)


```python
comparer.record_query(query = "Black metal", 
                      expected_text = "Black metal is an extreme subgenre of heavy metal music.")
comparer.record_query(query = "Tribulation", 
                      expected_text = "Tribulation are a Swedish heavy metal band from Arvika that formed in 2005.")
```


    Batches:   0%|          | 0/1 [00:00<?, ?it/s]



    Batches:   0%|          | 0/1 [00:00<?, ?it/s]


### 2. Comparing with expected results

#### 2.1 Initialize new comparison class


```python
comparer = ComparisonFrame()
```

    INFO:sentence_transformers.SentenceTransformer:Load pretrained SentenceTransformer: all-mpnet-base-v2
    INFO:sentence_transformers.SentenceTransformer:Use pytorch device: cpu


### 2.2 Show validation set


```python
untested_queries = comparer.get_all_queries(
    ## optionall
    untested_only=True)
print(untested_queries)
```

    ['Black metal', 'Tribulation']



```python
comparer.get_all_records()
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>id</th>
      <th>timestamp</th>
      <th>query</th>
      <th>expected_text</th>
      <th>tested</th>
      <th>test_status</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>1</td>
      <td>2023-11-06 00:49:46</td>
      <td>Black metal</td>
      <td>Black metal is an extreme subgenre of heavy me...</td>
      <td>no</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>1</th>
      <td>2</td>
      <td>2023-11-06 00:49:47</td>
      <td>Tribulation</td>
      <td>Tribulation are a Swedish heavy metal band fro...</td>
      <td>no</td>
      <td>NaN</td>
    </tr>
  </tbody>
</table>
</div>



#### 2.3 Compare newly generated with recorded


```python
valid_answer_query_1 = "Black metal is an extreme subgenre of heavy metal music."
very_similar_answer_query_1 = "Black metal is a subgenre of heavy metal music."
unexpected_answer_query_1 = "Black metals are beautiful and are often used in jewelry design."
```


```python
# with no entry to records
comparer.compare_with_record(query = "Black metal", 
                             provided_text = valid_answer_query_1, 
                             mark_as_tested=False)
comparer.compare_with_record(query = "Black metal", 
                             provided_text = very_similar_answer_query_1, 
                             mark_as_tested=False)
comparer.compare_with_record(query = "Black metal", 
                             provided_text = unexpected_answer_query_1, 
                             mark_as_tested=False)
```


    Batches:   0%|          | 0/1 [00:00<?, ?it/s]



    Batches:   0%|          | 0/1 [00:00<?, ?it/s]



    Batches:   0%|          | 0/1 [00:00<?, ?it/s]



    Batches:   0%|          | 0/1 [00:00<?, ?it/s]



    Batches:   0%|          | 0/1 [00:00<?, ?it/s]



    Batches:   0%|          | 0/1 [00:00<?, ?it/s]


#### 2.4 Check comparison results


```python
comparer.get_comparison_results()
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>query</th>
      <th>char_count_diff</th>
      <th>word_count_diff</th>
      <th>line_count_diff</th>
      <th>punctuation_diff</th>
      <th>semantic_similarity</th>
      <th>expected_text</th>
      <th>provided_text</th>
      <th>id</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>Black metal</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>1.000000</td>
      <td>Black metal is an extreme subgenre of heavy me...</td>
      <td>Black metal is an extreme subgenre of heavy me...</td>
      <td>1</td>
    </tr>
    <tr>
      <th>1</th>
      <td>Black metal</td>
      <td>9</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0.974236</td>
      <td>Black metal is an extreme subgenre of heavy me...</td>
      <td>Black metal is a subgenre of heavy metal music.</td>
      <td>1</td>
    </tr>
    <tr>
      <th>2</th>
      <td>Black metal</td>
      <td>8</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0.499244</td>
      <td>Black metal is an extreme subgenre of heavy me...</td>
      <td>Black metals are beautiful and are often used ...</td>
      <td>1</td>
    </tr>
  </tbody>
</table>
</div>



### 3. Record test statuses


```python
comparer.compare_with_record(query = "Black metal", 
                             provided_text = very_similar_answer_query_1, 
                             mark_as_tested=True)
```


    Batches:   0%|          | 0/1 [00:00<?, ?it/s]



    Batches:   0%|          | 0/1 [00:00<?, ?it/s]



```python
comparer.get_all_records()
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>id</th>
      <th>timestamp</th>
      <th>query</th>
      <th>expected_text</th>
      <th>tested</th>
      <th>test_status</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>1</td>
      <td>2023-11-06 00:49:46</td>
      <td>Black metal</td>
      <td>Black metal is an extreme subgenre of heavy me...</td>
      <td>yes</td>
      <td>pass</td>
    </tr>
    <tr>
      <th>1</th>
      <td>2</td>
      <td>2023-11-06 00:49:47</td>
      <td>Tribulation</td>
      <td>Tribulation are a Swedish heavy metal band fro...</td>
      <td>no</td>
      <td>NaN</td>
    </tr>
  </tbody>
</table>
</div>



### 4. Reseting and flushing results

#### 4.1 Reselt test statuses


```python
comparer.reset_record_statuses(
    # optionally
    record_ids = [1]
)
```


```python
comparer.get_all_records()
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>id</th>
      <th>timestamp</th>
      <th>query</th>
      <th>expected_text</th>
      <th>tested</th>
      <th>test_status</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>1</td>
      <td>2023-11-06 00:49:46</td>
      <td>Black metal</td>
      <td>Black metal is an extreme subgenre of heavy me...</td>
      <td>no</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>1</th>
      <td>2</td>
      <td>2023-11-06 00:49:47</td>
      <td>Tribulation</td>
      <td>Tribulation are a Swedish heavy metal band fro...</td>
      <td>no</td>
      <td>NaN</td>
    </tr>
  </tbody>
</table>
</div>



#### 4.2 Flush comparison results


```python
comparer.flush_comparison_results()
```


```python
comparer.get_comparison_results()
```

    ERROR:ComparisonFrame:No results file found. Please perform some comparisons first.


#### 4.3 Flush records


```python
comparer.flush_records()
```


```python
comparer.get_all_records()
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>id</th>
      <th>timestamp</th>
      <th>query</th>
      <th>expected_text</th>
      <th>tested</th>
      <th>test_status</th>
    </tr>
  </thead>
  <tbody>
  </tbody>
</table>
</div>


