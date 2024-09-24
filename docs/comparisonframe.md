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




    [{'record_id': '0cc157453395b440f36d1a1aee24aa76a03f5f9ab0a7a8bd7b663c92f2f16e87',
      'query': 'Black metal',
      'expected_text': 'Black metal is an extreme subgenre of heavy metal music.'},
     {'record_id': 'eecd9c2a5b25ee6053891b894157fa30372ed694763385e1ada1dc9ad8e41625',
      'query': 'Tribulation',
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
      <th>record_id</th>
      <th>query</th>
      <th>expected_text</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>0cc157453395b440f36d1a1aee24aa76a03f5f9ab0a7a8...</td>
      <td>Black metal</td>
      <td>Black metal is an extreme subgenre of heavy me...</td>
    </tr>
    <tr>
      <th>1</th>
      <td>eecd9c2a5b25ee6053891b894157fa30372ed694763385...</td>
      <td>Tribulation</td>
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




    [{'timestamp': '2024-09-24 03:43:48',
      'run_id': 'e8f5f87186ac81a38896e602c7d8a4e1b973aa00973b68cbfdc983e6c1762d6e',
      'query': 'Black metal',
      'provided_text': 'Black metal is an extreme subgenre of heavy metal music.'},
     {'timestamp': '2024-09-24 03:43:48',
      'run_id': 'e0e4dfaff0b16227dbfde7a75eb9f060ccd2b1b5acc8b4b48aa9d305a3591353',
      'query': 'Black metal',
      'provided_text': 'Black metal is a subgenre of heavy metal music.'},
     {'timestamp': '2024-09-24 03:43:48',
      'run_id': '4e806f8cf2bd2184e63d41c85322e129b14c8d5206472c7668077452386257af',
      'query': 'Black metal',
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
      <th>run_id</th>
      <th>query</th>
      <th>provided_text</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>2024-09-24 03:43:48</td>
      <td>e8f5f87186ac81a38896e602c7d8a4e1b973aa00973b68...</td>
      <td>Black metal</td>
      <td>Black metal is an extreme subgenre of heavy me...</td>
    </tr>
    <tr>
      <th>1</th>
      <td>2024-09-24 03:43:48</td>
      <td>e0e4dfaff0b16227dbfde7a75eb9f060ccd2b1b5acc8b4...</td>
      <td>Black metal</td>
      <td>Black metal is a subgenre of heavy metal music.</td>
    </tr>
    <tr>
      <th>2</th>
      <td>2024-09-24 03:43:48</td>
      <td>4e806f8cf2bd2184e63d41c85322e129b14c8d5206472c...</td>
      <td>Black metal</td>
      <td>Black metals are beautiful and are often used ...</td>
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




    [{'timestamp': '2024-09-24 03:43:57',
      'run_id': 'e8f5f87186ac81a38896e602c7d8a4e1b973aa00973b68cbfdc983e6c1762d6e',
      'query': 'Black metal',
      'provided_text': 'Black metal is an extreme subgenre of heavy metal music.',
      'record_id': '0cc157453395b440f36d1a1aee24aa76a03f5f9ab0a7a8bd7b663c92f2f16e87',
      'word_count_diff': 0,
      'semantic_similarity': 1.0000001192092896,
      'comparison_id': '9376f9245bf3a237ef1eb4920cc2c86918fdba5e5934014058b14286fbd31f32'},
     {'timestamp': '2024-09-24 03:43:57',
      'run_id': 'e0e4dfaff0b16227dbfde7a75eb9f060ccd2b1b5acc8b4b48aa9d305a3591353',
      'query': 'Black metal',
      'provided_text': 'Black metal is a subgenre of heavy metal music.',
      'record_id': '0cc157453395b440f36d1a1aee24aa76a03f5f9ab0a7a8bd7b663c92f2f16e87',
      'word_count_diff': 1,
      'semantic_similarity': 0.9859851002693176,
      'comparison_id': '756abbce6c86dea26ce9f3d0cc11668b76df40120faf2fbee1dad5daa1e201ec'},
     {'timestamp': '2024-09-24 03:43:57',
      'run_id': '4e806f8cf2bd2184e63d41c85322e129b14c8d5206472c7668077452386257af',
      'query': 'Black metal',
      'provided_text': 'Black metals are beautiful and are often used in jewelry design.',
      'record_id': '0cc157453395b440f36d1a1aee24aa76a03f5f9ab0a7a8bd7b663c92f2f16e87',
      'word_count_diff': 1,
      'semantic_similarity': 0.4940534234046936,
      'comparison_id': 'f6ab2967695a560f4ff208e03c2804b09f26b9356ab5da592186e503a900ab56'}]




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
      <th>run_id</th>
      <th>query</th>
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
      <td>2024-09-24 03:43:57</td>
      <td>e8f5f87186ac81a38896e602c7d8a4e1b973aa00973b68...</td>
      <td>Black metal</td>
      <td>Black metal is an extreme subgenre of heavy me...</td>
      <td>0cc157453395b440f36d1a1aee24aa76a03f5f9ab0a7a8...</td>
      <td>0</td>
      <td>1.000000</td>
      <td>9376f9245bf3a237ef1eb4920cc2c86918fdba5e593401...</td>
    </tr>
    <tr>
      <th>1</th>
      <td>2024-09-24 03:43:57</td>
      <td>e0e4dfaff0b16227dbfde7a75eb9f060ccd2b1b5acc8b4...</td>
      <td>Black metal</td>
      <td>Black metal is a subgenre of heavy metal music.</td>
      <td>0cc157453395b440f36d1a1aee24aa76a03f5f9ab0a7a8...</td>
      <td>1</td>
      <td>0.985985</td>
      <td>756abbce6c86dea26ce9f3d0cc11668b76df40120faf2f...</td>
    </tr>
    <tr>
      <th>2</th>
      <td>2024-09-24 03:43:57</td>
      <td>4e806f8cf2bd2184e63d41c85322e129b14c8d5206472c...</td>
      <td>Black metal</td>
      <td>Black metals are beautiful and are often used ...</td>
      <td>0cc157453395b440f36d1a1aee24aa76a03f5f9ab0a7a8...</td>
      <td>1</td>
      <td>0.494053</td>
      <td>f6ab2967695a560f4ff208e03c2804b09f26b9356ab5da...</td>
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




    [{'timestamp': '2024-09-24 03:44:07',
      'comparison_id': ['9376f9245bf3a237ef1eb4920cc2c86918fdba5e5934014058b14286fbd31f32',
       '756abbce6c86dea26ce9f3d0cc11668b76df40120faf2fbee1dad5daa1e201ec',
       'f6ab2967695a560f4ff208e03c2804b09f26b9356ab5da592186e503a900ab56'],
      'query': 'Black metal',
      'median_word_count_diff': 1.0,
      'median_semantic_similarity': 0.9859851002693176,
      'record_status_id': '2723311824179b0f89b65a513368bfe05298a625b7c73b5a06ff33702689d56a'}]




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
      <td>2024-09-24 03:44:07</td>
      <td>[9376f9245bf3a237ef1eb4920cc2c86918fdba5e59340...</td>
      <td>Black metal</td>
      <td>1.0</td>
      <td>0.985985</td>
      <td>2723311824179b0f89b65a513368bfe05298a625b7c73b...</td>
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




    [{'timestamp': '2024-09-24 03:44:13',
      'record_id': '0cc157453395b440f36d1a1aee24aa76a03f5f9ab0a7a8bd7b663c92f2f16e87',
      'record_status_id': '2723311824179b0f89b65a513368bfe05298a625b7c73b5a06ff33702689d56a',
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
      <td>2024-09-24 03:44:13</td>
      <td>0cc157453395b440f36d1a1aee24aa76a03f5f9ab0a7a8...</td>
      <td>2723311824179b0f89b65a513368bfe05298a625b7c73b...</td>
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
