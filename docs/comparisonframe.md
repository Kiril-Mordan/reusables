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
    ## provide filenames to persist state
    record_file = "record_file.csv",  # file where queries and expected results are stored
    results_file = "comparison_results.csv", # file where comparison results will be stored
)
```

#### 1.2 Recording queries and expected responses (validation set)


```python
comparer.record_query(query = "Black metal",
                      expected_text = "Black metal is an extreme subgenre of heavy metal music.")
comparer.record_query(query = "Tribulation",
                      expected_text = "Tribulation are a Swedish heavy metal band from Arvika that formed in 2005.")
```

### 2. Comparing with expected results

#### 2.1 Initialize new comparison class


```python
comparer = ComparisonFrame()
```

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
      <td>2024-07-01 02:22:37</td>
      <td>Black metal</td>
      <td>Black metal is an extreme subgenre of heavy me...</td>
      <td>no</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>1</th>
      <td>2</td>
      <td>2024-07-01 02:22:37</td>
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
      <td>0.985985</td>
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
      <td>0.494053</td>
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
      <td>2024-07-01 02:22:37</td>
      <td>Black metal</td>
      <td>Black metal is an extreme subgenre of heavy me...</td>
      <td>yes</td>
      <td>pass</td>
    </tr>
    <tr>
      <th>1</th>
      <td>2</td>
      <td>2024-07-01 02:22:37</td>
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
      <td>2024-07-01 02:22:37</td>
      <td>Black metal</td>
      <td>Black metal is an extreme subgenre of heavy me...</td>
      <td>no</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>1</th>
      <td>2</td>
      <td>2024-07-01 02:22:37</td>
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


