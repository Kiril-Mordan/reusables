```python
# import sys
# sys.path.append('../')
from comparisonframe import ComparisonFrame
```

    /home/kyriosskia/miniconda3/envs/testenv/lib/python3.10/site-packages/tqdm/auto.py:21: TqdmWarning: IProgress not found. Please update jupyter and ipywidgets. See https://ipywidgets.readthedocs.io/en/stable/user_install.html
      from .autonotebook import tqdm as notebook_tqdm


## Usage examples

The examples contain: 
1. Creating validation set and saving it to be reused
2. Comparing newly generated data with expected results 
3. Calculating aggregate comparison scores
4. Recording test statuses
5. Reseting statuses, flushing records and comparison results

### 1. Creating validation set

### 1.1 Initialize comparison class


```python
comparer = ComparisonFrame(
    # optionally
    ## mocker default parameters
    mocker_params = {
        'file_path' : "./comparisonframe_storage",
         'persist' : True},

    ## scores to calculate
    compare_scores = ['word_count_diff','semantic_similarity'],
    aggr_scores = ['median']
)
```

    /home/kyriosskia/miniconda3/envs/testenv/lib/python3.10/site-packages/transformers/tokenization_utils_base.py:1601: FutureWarning: `clean_up_tokenization_spaces` was not set. It will be set to `True` by default. This behavior will be depracted in transformers v4.45, and will be then set to `False` by default. For more details check this issue: https://github.com/huggingface/transformers/issues/31884
      warnings.warn(


#### 1.2 Recording queries and expected responses (validation set)


```python
comparer.record_queries(
    queries = ["Black metal", 
               "Tribulation"],
    expected_texts = ["Black metal is an extreme subgenre of heavy metal music.",
    "Tribulation are a Swedish heavy metal band from Arvika that formed in 2005."],
    metadata = {'name' : 'metal_bands'})
```

### 2. Comparing newly generated data with expected results 

#### 2.1 Initialize new comparison class


```python
comparer = ComparisonFrame(
    # optionally
    ## mocker default parameters
    mocker_params = {
        'file_path' : "./comparisonframe_storage",
         'persist' : True},

    ## scores to calculate
    compare_scores = ['word_count_diff','semantic_similarity'],
    aggr_scores = ['median']
)
```

### 2.2 Show validation set


```python
untested_queries = comparer.get_all_queries(
    ## optional
    metadata_filters={'name' : 'metal_bands'})
print(untested_queries)
```

    ['Black metal', 'Tribulation']



```python
comparer.get_all_records()
```




    [{'query': 'Black metal',
      'record_id': '0cc157453395b440f36d1a1aee24aa76a03f5f9ab0a7a8bd7b663c92f2f16e87',
      'expected_text': 'Black metal is an extreme subgenre of heavy metal music.'},
     {'query': 'Tribulation',
      'record_id': 'eecd9c2a5b25ee6053891b894157fa30372ed694763385e1ada1dc9ad8e41625',
      'expected_text': 'Tribulation are a Swedish heavy metal band from Arvika that formed in 2005.'}]




```python
comparer.get_all_records_df()
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
      <th>record_id</th>
      <th>expected_text</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>Black metal</td>
      <td>0cc157453395b440f36d1a1aee24aa76a03f5f9ab0a7a8...</td>
      <td>Black metal is an extreme subgenre of heavy me...</td>
    </tr>
    <tr>
      <th>1</th>
      <td>Tribulation</td>
      <td>eecd9c2a5b25ee6053891b894157fa30372ed694763385...</td>
      <td>Tribulation are a Swedish heavy metal band fro...</td>
    </tr>
  </tbody>
</table>
</div>



#### 2.3 Insert newly generated with records


```python
valid_answer_query_1 = "Black metal is an extreme subgenre of heavy metal music."
very_similar_answer_query_1 = "Black metal is a subgenre of heavy metal music."
unexpected_answer_query_1 = "Black metals are beautiful and are often used in jewelry design."
```


```python
comparer.record_runs(queries = ["Black metal"],
                     provided_texts = [valid_answer_query_1,
                                      very_similar_answer_query_1,
                                      unexpected_answer_query_1],
                    metadata={'desc' : 'definitions'})
```


```python
comparer.get_all_runs()
```




    [{'timestamp': '2024-08-22 21:27:45',
      'query': 'Black metal',
      'run_id': '1831f4f4b65bc287d27ff3bdc7bcbb5d9032b2d6b28602c202514a756eca3223',
      'provided_text': 'Black metal is an extreme subgenre of heavy metal music.'},
     {'timestamp': '2024-08-22 21:27:45',
      'query': 'Black metal',
      'run_id': 'dad65ebf45d7f54284f478e1850d258b8aabb66ba60ff31236666a4ede5260cc',
      'provided_text': 'Black metal is a subgenre of heavy metal music.'},
     {'timestamp': '2024-08-22 21:27:45',
      'query': 'Black metal',
      'run_id': 'e8432d75142df85bba1f3098403c6023a0f84ec5ef645c7a332c7033a78abcd1',
      'provided_text': 'Black metals are beautiful and are often used in jewelry design.'}]




```python
df = comparer.get_all_runs_df()
df
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
      <th>timestamp</th>
      <th>query</th>
      <th>run_id</th>
      <th>provided_text</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>2024-08-22 21:27:45</td>
      <td>Black metal</td>
      <td>1831f4f4b65bc287d27ff3bdc7bcbb5d9032b2d6b28602...</td>
      <td>Black metal is an extreme subgenre of heavy me...</td>
    </tr>
    <tr>
      <th>1</th>
      <td>2024-08-22 21:27:45</td>
      <td>Black metal</td>
      <td>dad65ebf45d7f54284f478e1850d258b8aabb66ba60ff3...</td>
      <td>Black metal is a subgenre of heavy metal music.</td>
    </tr>
    <tr>
      <th>2</th>
      <td>2024-08-22 21:27:45</td>
      <td>Black metal</td>
      <td>e8432d75142df85bba1f3098403c6023a0f84ec5ef645c...</td>
      <td>Black metals are beautiful and are often used ...</td>
    </tr>
  </tbody>
</table>
</div>



### 2.4 Comparing runs with records


```python
comparer.compare_runs_with_records()
```

    WARNING:ComparisonFrame:No data was found with applied filters!



```python
comparer.get_all_run_scores()
```




    [{'timestamp': '2024-08-22 21:27:57',
      'query': 'Black metal',
      'run_id': '1831f4f4b65bc287d27ff3bdc7bcbb5d9032b2d6b28602c202514a756eca3223',
      'provided_text': 'Black metal is an extreme subgenre of heavy metal music.',
      'record_id': '0cc157453395b440f36d1a1aee24aa76a03f5f9ab0a7a8bd7b663c92f2f16e87',
      'word_count_diff': 0,
      'semantic_similarity': 1.0000001192092896,
      'comparison_id': '25a7dab1af09323799699cd6d28529090072ee0808f1f1a4942c1db69c7b1621'},
     {'timestamp': '2024-08-22 21:27:57',
      'query': 'Black metal',
      'run_id': 'dad65ebf45d7f54284f478e1850d258b8aabb66ba60ff31236666a4ede5260cc',
      'provided_text': 'Black metal is a subgenre of heavy metal music.',
      'record_id': '0cc157453395b440f36d1a1aee24aa76a03f5f9ab0a7a8bd7b663c92f2f16e87',
      'word_count_diff': 1,
      'semantic_similarity': 0.9859851002693176,
      'comparison_id': '34611011b656a9495178dd833ce09c3afe6b9083abc47f1b42d43e1e76b143a4'},
     {'timestamp': '2024-08-22 21:27:57',
      'query': 'Black metal',
      'run_id': 'e8432d75142df85bba1f3098403c6023a0f84ec5ef645c7a332c7033a78abcd1',
      'provided_text': 'Black metals are beautiful and are often used in jewelry design.',
      'record_id': '0cc157453395b440f36d1a1aee24aa76a03f5f9ab0a7a8bd7b663c92f2f16e87',
      'word_count_diff': 1,
      'semantic_similarity': 0.4940534234046936,
      'comparison_id': '2fe5604e66d318a8195f4b3a9aa4548894a57972fbcc8386aaea3ee0ef02c071'}]




```python
comparer.get_all_run_scores_df()
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
      <th>timestamp</th>
      <th>query</th>
      <th>run_id</th>
      <th>provided_text</th>
      <th>record_id</th>
      <th>word_count_diff</th>
      <th>semantic_similarity</th>
      <th>comparison_id</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>2024-08-22 21:27:57</td>
      <td>Black metal</td>
      <td>1831f4f4b65bc287d27ff3bdc7bcbb5d9032b2d6b28602...</td>
      <td>Black metal is an extreme subgenre of heavy me...</td>
      <td>0cc157453395b440f36d1a1aee24aa76a03f5f9ab0a7a8...</td>
      <td>0</td>
      <td>1.000000</td>
      <td>25a7dab1af09323799699cd6d28529090072ee0808f1f1...</td>
    </tr>
    <tr>
      <th>1</th>
      <td>2024-08-22 21:27:57</td>
      <td>Black metal</td>
      <td>dad65ebf45d7f54284f478e1850d258b8aabb66ba60ff3...</td>
      <td>Black metal is a subgenre of heavy metal music.</td>
      <td>0cc157453395b440f36d1a1aee24aa76a03f5f9ab0a7a8...</td>
      <td>1</td>
      <td>0.985985</td>
      <td>34611011b656a9495178dd833ce09c3afe6b9083abc47f...</td>
    </tr>
    <tr>
      <th>2</th>
      <td>2024-08-22 21:27:57</td>
      <td>Black metal</td>
      <td>e8432d75142df85bba1f3098403c6023a0f84ec5ef645c...</td>
      <td>Black metals are beautiful and are often used ...</td>
      <td>0cc157453395b440f36d1a1aee24aa76a03f5f9ab0a7a8...</td>
      <td>1</td>
      <td>0.494053</td>
      <td>2fe5604e66d318a8195f4b3a9aa4548894a57972fbcc83...</td>
    </tr>
  </tbody>
</table>
</div>



### 3 Calculating aggregate comparison scores


```python
comparer.calculate_aggr_scores()
```

    WARNING:ComparisonFrame:No data was found with applied filters!



```python
comparer.get_all_aggr_scores()
```




    [{'timestamp': '2024-08-22 21:30:40',
      'comparison_id': ['25a7dab1af09323799699cd6d28529090072ee0808f1f1a4942c1db69c7b1621',
       '34611011b656a9495178dd833ce09c3afe6b9083abc47f1b42d43e1e76b143a4',
       '2fe5604e66d318a8195f4b3a9aa4548894a57972fbcc8386aaea3ee0ef02c071'],
      'query': 'Black metal',
      'median_word_count_diff': 1.0,
      'median_semantic_similarity': 0.9859851002693176,
      'record_status_id': 'd11f7522f4e4e34a6e6f387c6ce7572d43c69fef9f628e63d3f99c93cf0f4f7d'}]




```python
comparer.get_all_aggr_scores_df()
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
      <th>timestamp</th>
      <th>comparison_id</th>
      <th>query</th>
      <th>median_word_count_diff</th>
      <th>median_semantic_similarity</th>
      <th>record_status_id</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>2024-08-22 21:30:40</td>
      <td>[25a7dab1af09323799699cd6d28529090072ee0808f1f...</td>
      <td>Black metal</td>
      <td>1.0</td>
      <td>0.985985</td>
      <td>d11f7522f4e4e34a6e6f387c6ce7572d43c69fef9f628e...</td>
    </tr>
  </tbody>
</table>
</div>



### 4. Recording test statuses


```python
comparer.calculate_test_statuses(test_query = "median_semantic_similarity > 0.9")

```


```python
comparer.get_test_statuses()
```




    [{'timestamp': '2024-08-22 21:31:18',
      'record_id': '0cc157453395b440f36d1a1aee24aa76a03f5f9ab0a7a8bd7b663c92f2f16e87',
      'record_status_id': 'd11f7522f4e4e34a6e6f387c6ce7572d43c69fef9f628e63d3f99c93cf0f4f7d',
      'query': 'Black metal',
      'valid': True},
     {'timestamp': '2024-08-22 21:31:51',
      'record_id': '0cc157453395b440f36d1a1aee24aa76a03f5f9ab0a7a8bd7b663c92f2f16e87',
      'record_status_id': 'd11f7522f4e4e34a6e6f387c6ce7572d43c69fef9f628e63d3f99c93cf0f4f7d',
      'query': 'Black metal',
      'valid': True},
     {'timestamp': '2024-08-22 21:36:59',
      'record_id': '0cc157453395b440f36d1a1aee24aa76a03f5f9ab0a7a8bd7b663c92f2f16e87',
      'record_status_id': 'd11f7522f4e4e34a6e6f387c6ce7572d43c69fef9f628e63d3f99c93cf0f4f7d',
      'query': 'Black metal',
      'valid': False}]




```python
comparer.get_test_statuses_df()
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
      <th>timestamp</th>
      <th>record_id</th>
      <th>record_status_id</th>
      <th>query</th>
      <th>valid</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>2024-08-22 21:31:18</td>
      <td>0cc157453395b440f36d1a1aee24aa76a03f5f9ab0a7a8...</td>
      <td>d11f7522f4e4e34a6e6f387c6ce7572d43c69fef9f628e...</td>
      <td>Black metal</td>
      <td>True</td>
    </tr>
    <tr>
      <th>1</th>
      <td>2024-08-22 21:31:51</td>
      <td>0cc157453395b440f36d1a1aee24aa76a03f5f9ab0a7a8...</td>
      <td>d11f7522f4e4e34a6e6f387c6ce7572d43c69fef9f628e...</td>
      <td>Black metal</td>
      <td>True</td>
    </tr>
    <tr>
      <th>2</th>
      <td>2024-08-22 21:36:59</td>
      <td>0cc157453395b440f36d1a1aee24aa76a03f5f9ab0a7a8...</td>
      <td>d11f7522f4e4e34a6e6f387c6ce7572d43c69fef9f628e...</td>
      <td>Black metal</td>
      <td>False</td>
    </tr>
  </tbody>
</table>
</div>



### 5. Reseting statuses, flushing records and comparison results


```python
comparer.flush_records()
```


```python
comparer.flush_runs()
```


```python
comparer.flush_comparison_scores()
```


```python
comparer.flush_aggregate_scores()
```


```python
comparer.flush_test_statuses()
```
