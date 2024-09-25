```python
from comparisonframe import ComparisonFrame
```

### 1. Creating validation set

#### 1.1 Initialize comparison class


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

    /home/kyriosskia/miniforge3/envs/testenv/lib/python3.10/site-packages/transformers/tokenization_utils_base.py:1601: FutureWarning: `clean_up_tokenization_spaces` was not set. It will be set to `True` by default. This behavior will be depracted in transformers v4.45, and will be then set to `False` by default. For more details check this issue: https://github.com/huggingface/transformers/issues/31884
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




    [{'expected_text': 'Black metal is an extreme subgenre of heavy metal music.',
      'record_id': '0cc157453395b440f36d1a1aee24aa76a03f5f9ab0a7a8bd7b663c92f2f16e87',
      'query': 'Black metal'},
     {'expected_text': 'Tribulation are a Swedish heavy metal band from Arvika that formed in 2005.',
      'record_id': 'eecd9c2a5b25ee6053891b894157fa30372ed694763385e1ada1dc9ad8e41625',
      'query': 'Tribulation'}]




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
      <th>expected_text</th>
      <th>record_id</th>
      <th>query</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>Black metal is an extreme subgenre of heavy me...</td>
      <td>0cc157453395b440f36d1a1aee24aa76a03f5f9ab0a7a8...</td>
      <td>Black metal</td>
    </tr>
    <tr>
      <th>1</th>
      <td>Tribulation are a Swedish heavy metal band fro...</td>
      <td>eecd9c2a5b25ee6053891b894157fa30372ed694763385...</td>
      <td>Tribulation</td>
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




    [{'query': 'Black metal',
      'provided_text': 'Black metal is an extreme subgenre of heavy metal music.',
      'run_id': 'faf5aab28ee8d460cbb69c6f434bee622aff8cdfb8796282bdc547fff2c1abf8',
      'timestamp': '2024-09-26 01:36:13'},
     {'query': 'Black metal',
      'provided_text': 'Black metal is a subgenre of heavy metal music.',
      'run_id': '9fbd80050d382972c012ffcb4641f48d6220afb2210a20a11da5c7a48664f033',
      'timestamp': '2024-09-26 01:36:13'},
     {'query': 'Black metal',
      'provided_text': 'Black metals are beautiful and are often used in jewelry design.',
      'run_id': 'e4fc3f56c95d4266b6543a306c4305e0d8b960a1e0196d05cfc8ee4ea0bd7129',
      'timestamp': '2024-09-26 01:36:13'}]




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
      <th>query</th>
      <th>provided_text</th>
      <th>run_id</th>
      <th>timestamp</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>Black metal</td>
      <td>Black metal is an extreme subgenre of heavy me...</td>
      <td>faf5aab28ee8d460cbb69c6f434bee622aff8cdfb87962...</td>
      <td>2024-09-26 01:36:13</td>
    </tr>
    <tr>
      <th>1</th>
      <td>Black metal</td>
      <td>Black metal is a subgenre of heavy metal music.</td>
      <td>9fbd80050d382972c012ffcb4641f48d6220afb2210a20...</td>
      <td>2024-09-26 01:36:13</td>
    </tr>
    <tr>
      <th>2</th>
      <td>Black metal</td>
      <td>Black metals are beautiful and are often used ...</td>
      <td>e4fc3f56c95d4266b6543a306c4305e0d8b960a1e0196d...</td>
      <td>2024-09-26 01:36:13</td>
    </tr>
  </tbody>
</table>
</div>



#### 2.4 Comparing runs with records


```python
comparer.compare_runs_with_records()
```

    WARNING:ComparisonFrame:No data was found with applied filters!



```python
comparer.get_all_run_scores()
```




    [{'query': 'Black metal',
      'provided_text': 'Black metal is an extreme subgenre of heavy metal music.',
      'run_id': 'faf5aab28ee8d460cbb69c6f434bee622aff8cdfb8796282bdc547fff2c1abf8',
      'timestamp': '2024-09-26 01:36:13',
      'record_id': '0cc157453395b440f36d1a1aee24aa76a03f5f9ab0a7a8bd7b663c92f2f16e87',
      'word_count_diff': 0,
      'semantic_similarity': 0.9999999403953552,
      'comparison_id': 'cdb16a8d16a95e85d879c29aaf9762c9e2776843f2a01d6ef9154daacd9b732d'},
     {'query': 'Black metal',
      'provided_text': 'Black metal is a subgenre of heavy metal music.',
      'run_id': '9fbd80050d382972c012ffcb4641f48d6220afb2210a20a11da5c7a48664f033',
      'timestamp': '2024-09-26 01:36:13',
      'record_id': '0cc157453395b440f36d1a1aee24aa76a03f5f9ab0a7a8bd7b663c92f2f16e87',
      'word_count_diff': 1,
      'semantic_similarity': 0.9859851002693176,
      'comparison_id': '16472e44ac7d2d74e18ea583490c2f6b8661cc8b48cc9b7480a51dc8c6796c41'},
     {'query': 'Black metal',
      'provided_text': 'Black metals are beautiful and are often used in jewelry design.',
      'run_id': 'e4fc3f56c95d4266b6543a306c4305e0d8b960a1e0196d05cfc8ee4ea0bd7129',
      'timestamp': '2024-09-26 01:36:13',
      'record_id': '0cc157453395b440f36d1a1aee24aa76a03f5f9ab0a7a8bd7b663c92f2f16e87',
      'word_count_diff': 1,
      'semantic_similarity': 0.4940534234046936,
      'comparison_id': '966c1da5e641480e8ccd33a7d0f544d9ec6c4e2e799be11529d2cf7a222deb9a'}]




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
      <th>query</th>
      <th>provided_text</th>
      <th>run_id</th>
      <th>timestamp</th>
      <th>record_id</th>
      <th>word_count_diff</th>
      <th>semantic_similarity</th>
      <th>comparison_id</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>Black metal</td>
      <td>Black metal is an extreme subgenre of heavy me...</td>
      <td>faf5aab28ee8d460cbb69c6f434bee622aff8cdfb87962...</td>
      <td>2024-09-26 01:36:13</td>
      <td>0cc157453395b440f36d1a1aee24aa76a03f5f9ab0a7a8...</td>
      <td>0</td>
      <td>1.000000</td>
      <td>cdb16a8d16a95e85d879c29aaf9762c9e2776843f2a01d...</td>
    </tr>
    <tr>
      <th>1</th>
      <td>Black metal</td>
      <td>Black metal is a subgenre of heavy metal music.</td>
      <td>9fbd80050d382972c012ffcb4641f48d6220afb2210a20...</td>
      <td>2024-09-26 01:36:13</td>
      <td>0cc157453395b440f36d1a1aee24aa76a03f5f9ab0a7a8...</td>
      <td>1</td>
      <td>0.985985</td>
      <td>16472e44ac7d2d74e18ea583490c2f6b8661cc8b48cc9b...</td>
    </tr>
    <tr>
      <th>2</th>
      <td>Black metal</td>
      <td>Black metals are beautiful and are often used ...</td>
      <td>e4fc3f56c95d4266b6543a306c4305e0d8b960a1e0196d...</td>
      <td>2024-09-26 01:36:13</td>
      <td>0cc157453395b440f36d1a1aee24aa76a03f5f9ab0a7a8...</td>
      <td>1</td>
      <td>0.494053</td>
      <td>966c1da5e641480e8ccd33a7d0f544d9ec6c4e2e799be1...</td>
    </tr>
  </tbody>
</table>
</div>



### 3 Calculating aggregate comparison scores


```python
comparer.calculate_aggr_scores(group_by = ['desc'])
```

    WARNING:ComparisonFrame:No data was found with applied filters!



```python
comparer.get_all_aggr_scores()
```




    [{'timestamp': '2024-09-26 01:36:13',
      'comparison_id': ['cdb16a8d16a95e85d879c29aaf9762c9e2776843f2a01d6ef9154daacd9b732d',
       '16472e44ac7d2d74e18ea583490c2f6b8661cc8b48cc9b7480a51dc8c6796c41',
       '966c1da5e641480e8ccd33a7d0f544d9ec6c4e2e799be11529d2cf7a222deb9a'],
      'query': ['Black metal'],
      'grouped_by': ['query'],
      'group': {'query': 'Black metal'},
      'median_word_count_diff': 1.0,
      'median_semantic_similarity': 0.9859851002693176,
      'record_status_id': 'dc1126e128d42f74bb98bad9ce4101fe1a4ea5a46df57d430dea99fdd4b8c628'}]




```python
comparer.get_all_aggr_scores_df(grouped_by = ['desc'])
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
      <th>grouped_by</th>
      <th>group</th>
      <th>median_word_count_diff</th>
      <th>median_semantic_similarity</th>
      <th>record_status_id</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>2024-09-26 01:36:13</td>
      <td>[cdb16a8d16a95e85d879c29aaf9762c9e2776843f2a01...</td>
      <td>[Black metal]</td>
      <td>[desc]</td>
      <td>{'desc': 'definitions'}</td>
      <td>1.0</td>
      <td>0.985985</td>
      <td>c9d97729c5b03641fbf8fd35d257f2f1024a812f097ffb...</td>
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




    [{'timestamp': '2024-09-26 01:36:13',
      'record_id': '0cc157453395b440f36d1a1aee24aa76a03f5f9ab0a7a8bd7b663c92f2f16e87',
      'record_status_id': 'dc1126e128d42f74bb98bad9ce4101fe1a4ea5a46df57d430dea99fdd4b8c628',
      'query': 'Black metal',
      'test': 'median_semantic_similarity > 0.9',
      'valid': True}]




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
      <th>test</th>
      <th>valid</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>2024-09-26 01:36:13</td>
      <td>0cc157453395b440f36d1a1aee24aa76a03f5f9ab0a7a8...</td>
      <td>dc1126e128d42f74bb98bad9ce4101fe1a4ea5a46df57d...</td>
      <td>Black metal</td>
      <td>median_semantic_similarity &gt; 0.9</td>
      <td>True</td>
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
