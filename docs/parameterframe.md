# Parameterframe

The module provides an interface for managing solution parameters.
It allows for the structured storage and retrieval of parameter sets from a database.



```python
import sys
import pandas as pd
import os
sys.path.append('../')
from python_modules.parameterframe import FileTypeHandler, ParameterFrame, DatabaseConnector

```

## Content

1. Processing and reconstructing yaml and txt with FileTypeHandler
2. Assembling parameter sets and adding to solution with ParameterFrame
3. Commiting and pushing solutions with DatabaseConnector

### 1. Processing and reconstructing yaml and txt with FileTypeHandler


```python
params_path = "../tests/parameterframe/example_configs"

pf = ParameterFrame(
    params_path = params_path
)

pf.process_parameters_from_files()
```

### 2. Assembling parameter sets and adding to solution with ParameterFrame


```python
pf.make_parameter_set(
    parameter_set_name="test_set",
    parameter_set_description="example parameters for test purposes",
    parameter_names=['param_1','param_2','param_10', 'param_11','param_21']
)
```


```python
pf.add_solution_description(solution_name = "example_solution",
                            solution_description = "example solution for test")
```


```python
pf.solutions['example_solution']
```




    {'solution_id': 'ffb2fa4d1f14786e7a11641a870c3db55f08f375fb7ac00c9a2127f7cd801a60',
     'solution_description': {'solution_id': 'ffb2fa4d1f14786e7a11641a870c3db55f08f375fb7ac00c9a2127f7cd801a60',
      'solution_name': 'example_solution',
      'solution_description': 'example solution for test',
      'deployment_date': None,
      'deprication_date': None,
      'maintainers': None}}




```python
pf.add_parameter_set_to_solution(solution_name="example_solution",
                                 parameter_set_name="test_set")
```


```python
pd.DataFrame([pf.solutions['example_solution']['solution_parameter_set']['test_set']])
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
      <th>solution_id</th>
      <th>parameter_set_id</th>
      <th>deployment_status</th>
      <th>insertion_datetime</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>ffb2fa4d1f14786e7a11641a870c3db55f08f375fb7ac0...</td>
      <td>a54f04d2ff154294309403206e059aec556cdcfa511206...</td>
      <td>STAGING</td>
      <td>2024-04-21 23:18:22</td>
    </tr>
  </tbody>
</table>
</div>



### 3. Commiting solutions with DatabaseConnector


```python
pf.commit_solution(solution_name="example_solution",
                    parameter_set_names=["test_set"])
```

#### solution_description


```python
pd.DataFrame(pf.commited_tables['ffb2fa4d1f14786e7a11641a870c3db55f08f375fb7ac00c9a2127f7cd801a60']['solution_description'])
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
      <th>solution_id</th>
      <th>solution_name</th>
      <th>solution_description</th>
      <th>deployment_date</th>
      <th>deprication_date</th>
      <th>maintainers</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>ffb2fa4d1f14786e7a11641a870c3db55f08f375fb7ac0...</td>
      <td>example_solution</td>
      <td>example solution for test</td>
      <td>None</td>
      <td>None</td>
      <td>None</td>
    </tr>
  </tbody>
</table>
</div>



#### solution_parameter_set


```python
param_set_id = 'a54f04d2ff154294309403206e059aec556cdcfa51120649ce663f3230a970d5'

pd.DataFrame(pf.commited_tables['ffb2fa4d1f14786e7a11641a870c3db55f08f375fb7ac00c9a2127f7cd801a60']['solution_parameter_set'][param_set_id])
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
      <th>solution_id</th>
      <th>parameter_set_id</th>
      <th>deployment_status</th>
      <th>insertion_datetime</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>ffb2fa4d1f14786e7a11641a870c3db55f08f375fb7ac0...</td>
      <td>a54f04d2ff154294309403206e059aec556cdcfa511206...</td>
      <td>STAGING</td>
      <td>2024-04-21 23:18:22</td>
    </tr>
  </tbody>
</table>
</div>



#### parameter_set


```python
pd.DataFrame(pf.commited_tables['ffb2fa4d1f14786e7a11641a870c3db55f08f375fb7ac00c9a2127f7cd801a60']\
    ['parameter_set']\
        [param_set_id])
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
      <th>parameter_set_id</th>
      <th>parameter_id</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>a54f04d2ff154294309403206e059aec556cdcfa511206...</td>
      <td>4cea5b09e77da310c5105978f2ceea5c5d8c9c7b65d0e0...</td>
    </tr>
    <tr>
      <th>1</th>
      <td>a54f04d2ff154294309403206e059aec556cdcfa511206...</td>
      <td>bf11768decb1d0204e2636edd05c354573d473e67f1b04...</td>
    </tr>
    <tr>
      <th>2</th>
      <td>a54f04d2ff154294309403206e059aec556cdcfa511206...</td>
      <td>9a4a3ace265c9bf2facc0044ca24260c42805c6e7b2a60...</td>
    </tr>
    <tr>
      <th>3</th>
      <td>a54f04d2ff154294309403206e059aec556cdcfa511206...</td>
      <td>ace2f31433212fbf9e764069a30a7675ca78f496d31f06...</td>
    </tr>
    <tr>
      <th>4</th>
      <td>a54f04d2ff154294309403206e059aec556cdcfa511206...</td>
      <td>1a4f19ee9e186ee739daecbc778501c5851d3fb5d05c4a...</td>
    </tr>
  </tbody>
</table>
</div>



#### parameter_set_description


```python
pd.DataFrame(pf.commited_tables['ffb2fa4d1f14786e7a11641a870c3db55f08f375fb7ac00c9a2127f7cd801a60']\
    ['parameter_set_description']\
        [param_set_id])
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
      <th>parameter_set_id</th>
      <th>parameter_set_name</th>
      <th>parameter_set_description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>a54f04d2ff154294309403206e059aec556cdcfa511206...</td>
      <td>test_set</td>
      <td>example parameters for test purposes</td>
    </tr>
  </tbody>
</table>
</div>



#### parameter_description


```python
pf.commited_tables['ffb2fa4d1f14786e7a11641a870c3db55f08f375fb7ac00c9a2127f7cd801a60']['parameter_description'][param_set_id]
```




    {'4cea5b09e77da310c5105978f2ceea5c5d8c9c7b65d0e00b45135ea90fc011af': [{'parameter_id': '4cea5b09e77da310c5105978f2ceea5c5d8c9c7b65d0e00b45135ea90fc011af',
       'parameter_name': 'param_1',
       'parameter_description': '',
       'file_name': 'param_1.yaml',
       'file_type': 'yaml'}],
     'bf11768decb1d0204e2636edd05c354573d473e67f1b048369b2ee99c865bf5f': [{'parameter_id': 'bf11768decb1d0204e2636edd05c354573d473e67f1b048369b2ee99c865bf5f',
       'parameter_name': 'param_2',
       'parameter_description': '',
       'file_name': 'param_2.yaml',
       'file_type': 'yaml'}],
     '9a4a3ace265c9bf2facc0044ca24260c42805c6e7b2a608dfd2f56a54d9d36be': [{'parameter_id': '9a4a3ace265c9bf2facc0044ca24260c42805c6e7b2a608dfd2f56a54d9d36be',
       'parameter_name': 'param_10',
       'parameter_description': '',
       'file_name': 'param_10.txt',
       'file_type': 'txt'}],
     'ace2f31433212fbf9e764069a30a7675ca78f496d31f061d06d0a0420fc52768': [{'parameter_id': 'ace2f31433212fbf9e764069a30a7675ca78f496d31f061d06d0a0420fc52768',
       'parameter_name': 'param_11',
       'parameter_description': '',
       'file_name': 'param_11.dill',
       'file_type': 'unknown'}],
     '1a4f19ee9e186ee739daecbc778501c5851d3fb5d05c4a3c1200e599855e8689': [{'parameter_id': '1a4f19ee9e186ee739daecbc778501c5851d3fb5d05c4a3c1200e599855e8689',
       'parameter_name': 'param_21',
       'parameter_description': '',
       'file_name': 'param_21.ipynb',
       'file_type': 'unknown'}]}



#### parameter_description


```python
pd.DataFrame([tab for param_id, tab_list in pf.commited_tables['ffb2fa4d1f14786e7a11641a870c3db55f08f375fb7ac00c9a2127f7cd801a60']\
    ['parameter_description']\
        [param_set_id].items()\
            for tab in tab_list])
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
      <th>parameter_id</th>
      <th>parameter_name</th>
      <th>parameter_description</th>
      <th>file_name</th>
      <th>file_type</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>4cea5b09e77da310c5105978f2ceea5c5d8c9c7b65d0e0...</td>
      <td>param_1</td>
      <td></td>
      <td>param_1.yaml</td>
      <td>yaml</td>
    </tr>
    <tr>
      <th>1</th>
      <td>bf11768decb1d0204e2636edd05c354573d473e67f1b04...</td>
      <td>param_2</td>
      <td></td>
      <td>param_2.yaml</td>
      <td>yaml</td>
    </tr>
    <tr>
      <th>2</th>
      <td>9a4a3ace265c9bf2facc0044ca24260c42805c6e7b2a60...</td>
      <td>param_10</td>
      <td></td>
      <td>param_10.txt</td>
      <td>txt</td>
    </tr>
    <tr>
      <th>3</th>
      <td>ace2f31433212fbf9e764069a30a7675ca78f496d31f06...</td>
      <td>param_11</td>
      <td></td>
      <td>param_11.dill</td>
      <td>unknown</td>
    </tr>
    <tr>
      <th>4</th>
      <td>1a4f19ee9e186ee739daecbc778501c5851d3fb5d05c4a...</td>
      <td>param_21</td>
      <td></td>
      <td>param_21.ipynb</td>
      <td>unknown</td>
    </tr>
  </tbody>
</table>
</div>



#### parameter_attribute


```python
pd.DataFrame([tab for param_id, tab_list in pf.commited_tables['ffb2fa4d1f14786e7a11641a870c3db55f08f375fb7ac00c9a2127f7cd801a60']\
    ['parameter_attribute']\
        [param_set_id].items() \
            for tab in tab_list])
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
      <th>parameter_id</th>
      <th>attribute_id</th>
      <th>previous_attribute_id</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>4cea5b09e77da310c5105978f2ceea5c5d8c9c7b65d0e0...</td>
      <td>ee25af17445d7622cbf61a5b9424246a1f3104704b68bd...</td>
      <td>None</td>
    </tr>
    <tr>
      <th>1</th>
      <td>4cea5b09e77da310c5105978f2ceea5c5d8c9c7b65d0e0...</td>
      <td>8b5b2be24e60ba407b90967820da8a1385a6d67691a02b...</td>
      <td>None</td>
    </tr>
    <tr>
      <th>2</th>
      <td>4cea5b09e77da310c5105978f2ceea5c5d8c9c7b65d0e0...</td>
      <td>52ea872c99c586530348ba8902dcab831761673d25cf1c...</td>
      <td>None</td>
    </tr>
    <tr>
      <th>3</th>
      <td>bf11768decb1d0204e2636edd05c354573d473e67f1b04...</td>
      <td>7d5ee0e0cd00c3703e5f346c6887baf503faaf9fe09077...</td>
      <td>None</td>
    </tr>
    <tr>
      <th>4</th>
      <td>bf11768decb1d0204e2636edd05c354573d473e67f1b04...</td>
      <td>ee25af17445d7622cbf61a5b9424246a1f3104704b68bd...</td>
      <td>7d5ee0e0cd00c3703e5f346c6887baf503faaf9fe09077...</td>
    </tr>
    <tr>
      <th>5</th>
      <td>bf11768decb1d0204e2636edd05c354573d473e67f1b04...</td>
      <td>3367512147bf19ae99c986b356af11dcdc067376aa1b79...</td>
      <td>7d5ee0e0cd00c3703e5f346c6887baf503faaf9fe09077...</td>
    </tr>
    <tr>
      <th>6</th>
      <td>bf11768decb1d0204e2636edd05c354573d473e67f1b04...</td>
      <td>341769820d8937a5c9f9b980eefca37f3f37fcc6fd01c6...</td>
      <td>7d5ee0e0cd00c3703e5f346c6887baf503faaf9fe09077...</td>
    </tr>
    <tr>
      <th>7</th>
      <td>bf11768decb1d0204e2636edd05c354573d473e67f1b04...</td>
      <td>2e8b00e571f9d835d3f022a9ff49b9779034ab21bffdcd...</td>
      <td>341769820d8937a5c9f9b980eefca37f3f37fcc6fd01c6...</td>
    </tr>
    <tr>
      <th>8</th>
      <td>bf11768decb1d0204e2636edd05c354573d473e67f1b04...</td>
      <td>ecd93cf051988b23b3590415f4e7d550de264600d7d2af...</td>
      <td>341769820d8937a5c9f9b980eefca37f3f37fcc6fd01c6...</td>
    </tr>
    <tr>
      <th>9</th>
      <td>9a4a3ace265c9bf2facc0044ca24260c42805c6e7b2a60...</td>
      <td>fa4e8d81f4dbe6d306aff59bea4693d325a203be5d5b9f...</td>
      <td>None</td>
    </tr>
    <tr>
      <th>10</th>
      <td>9a4a3ace265c9bf2facc0044ca24260c42805c6e7b2a60...</td>
      <td>c26e7e96f0f3647c159b0934f4dc55207ac059abb56005...</td>
      <td>fa4e8d81f4dbe6d306aff59bea4693d325a203be5d5b9f...</td>
    </tr>
    <tr>
      <th>11</th>
      <td>9a4a3ace265c9bf2facc0044ca24260c42805c6e7b2a60...</td>
      <td>f7cd339f77c1799f399d8ebcbb27f2d41a448622254d64...</td>
      <td>c26e7e96f0f3647c159b0934f4dc55207ac059abb56005...</td>
    </tr>
    <tr>
      <th>12</th>
      <td>9a4a3ace265c9bf2facc0044ca24260c42805c6e7b2a60...</td>
      <td>15a33fe62774a1857b404f453ba1195eb4355e10bc9519...</td>
      <td>f7cd339f77c1799f399d8ebcbb27f2d41a448622254d64...</td>
    </tr>
    <tr>
      <th>13</th>
      <td>9a4a3ace265c9bf2facc0044ca24260c42805c6e7b2a60...</td>
      <td>99761e3d58bc213dc3ab33f2dc8dabe5f97d3aea6b59cd...</td>
      <td>15a33fe62774a1857b404f453ba1195eb4355e10bc9519...</td>
    </tr>
    <tr>
      <th>14</th>
      <td>9a4a3ace265c9bf2facc0044ca24260c42805c6e7b2a60...</td>
      <td>036a9c122c1f4c9304afa23c4d1fce5224c270a206889a...</td>
      <td>99761e3d58bc213dc3ab33f2dc8dabe5f97d3aea6b59cd...</td>
    </tr>
    <tr>
      <th>15</th>
      <td>9a4a3ace265c9bf2facc0044ca24260c42805c6e7b2a60...</td>
      <td>e72aa8015688052f4e7fddbf4c74e5bf2bd74239ebf390...</td>
      <td>036a9c122c1f4c9304afa23c4d1fce5224c270a206889a...</td>
    </tr>
    <tr>
      <th>16</th>
      <td>9a4a3ace265c9bf2facc0044ca24260c42805c6e7b2a60...</td>
      <td>0ae8eda3dbeedbc17e27a679c5426dd3af1434f7c37b4e...</td>
      <td>e72aa8015688052f4e7fddbf4c74e5bf2bd74239ebf390...</td>
    </tr>
    <tr>
      <th>17</th>
      <td>9a4a3ace265c9bf2facc0044ca24260c42805c6e7b2a60...</td>
      <td>cedcfbb0d95798514b6aaf30118fff7b46f863f1bc8b80...</td>
      <td>0ae8eda3dbeedbc17e27a679c5426dd3af1434f7c37b4e...</td>
    </tr>
    <tr>
      <th>18</th>
      <td>ace2f31433212fbf9e764069a30a7675ca78f496d31f06...</td>
      <td>ace2f31433212fbf9e764069a30a7675ca78f496d31f06...</td>
      <td>None</td>
    </tr>
    <tr>
      <th>19</th>
      <td>1a4f19ee9e186ee739daecbc778501c5851d3fb5d05c4a...</td>
      <td>87d93e1862f0f58199c3fcb7114b92fe59f03581804b1c...</td>
      <td>None</td>
    </tr>
    <tr>
      <th>20</th>
      <td>1a4f19ee9e186ee739daecbc778501c5851d3fb5d05c4a...</td>
      <td>b4a705d09aa0361f4db453da32abb05a5c4e0249d6180d...</td>
      <td>87d93e1862f0f58199c3fcb7114b92fe59f03581804b1c...</td>
    </tr>
    <tr>
      <th>21</th>
      <td>1a4f19ee9e186ee739daecbc778501c5851d3fb5d05c4a...</td>
      <td>e4e2c33a2ea67f34bf3ac1e9d99edaad501c7dc4ea82f4...</td>
      <td>b4a705d09aa0361f4db453da32abb05a5c4e0249d6180d...</td>
    </tr>
    <tr>
      <th>22</th>
      <td>1a4f19ee9e186ee739daecbc778501c5851d3fb5d05c4a...</td>
      <td>777abf12375b7f605b21535eb0d6232ce99581c6d2b117...</td>
      <td>e4e2c33a2ea67f34bf3ac1e9d99edaad501c7dc4ea82f4...</td>
    </tr>
  </tbody>
</table>
</div>




```python
pf.commited_tables['ffb2fa4d1f14786e7a11641a870c3db55f08f375fb7ac00c9a2127f7cd801a60']\
    ['parameter_attribute']\
        [param_set_id]
```




    {'4cea5b09e77da310c5105978f2ceea5c5d8c9c7b65d0e00b45135ea90fc011af': [{'parameter_id': '4cea5b09e77da310c5105978f2ceea5c5d8c9c7b65d0e00b45135ea90fc011af',
       'attribute_id': 'ee25af17445d7622cbf61a5b9424246a1f3104704b68bd31b9b7532471d492e5',
       'previous_attribute_id': None},
      {'parameter_id': '4cea5b09e77da310c5105978f2ceea5c5d8c9c7b65d0e00b45135ea90fc011af',
       'attribute_id': '8b5b2be24e60ba407b90967820da8a1385a6d67691a02bc663703160ef655101',
       'previous_attribute_id': None},
      {'parameter_id': '4cea5b09e77da310c5105978f2ceea5c5d8c9c7b65d0e00b45135ea90fc011af',
       'attribute_id': '52ea872c99c586530348ba8902dcab831761673d25cf1cb0023576820289ce6b',
       'previous_attribute_id': None}],
     'bf11768decb1d0204e2636edd05c354573d473e67f1b048369b2ee99c865bf5f': [{'parameter_id': 'bf11768decb1d0204e2636edd05c354573d473e67f1b048369b2ee99c865bf5f',
       'attribute_id': '7d5ee0e0cd00c3703e5f346c6887baf503faaf9fe090774f6866311f4fa34179',
       'previous_attribute_id': None},
      {'parameter_id': 'bf11768decb1d0204e2636edd05c354573d473e67f1b048369b2ee99c865bf5f',
       'attribute_id': 'ee25af17445d7622cbf61a5b9424246a1f3104704b68bd31b9b7532471d492e5',
       'previous_attribute_id': '7d5ee0e0cd00c3703e5f346c6887baf503faaf9fe090774f6866311f4fa34179'},
      {'parameter_id': 'bf11768decb1d0204e2636edd05c354573d473e67f1b048369b2ee99c865bf5f',
       'attribute_id': '3367512147bf19ae99c986b356af11dcdc067376aa1b79eb8ba8f61324e8dc18',
       'previous_attribute_id': '7d5ee0e0cd00c3703e5f346c6887baf503faaf9fe090774f6866311f4fa34179'},
      {'parameter_id': 'bf11768decb1d0204e2636edd05c354573d473e67f1b048369b2ee99c865bf5f',
       'attribute_id': '341769820d8937a5c9f9b980eefca37f3f37fcc6fd01c6f4c930fdb9d5dd5128',
       'previous_attribute_id': '7d5ee0e0cd00c3703e5f346c6887baf503faaf9fe090774f6866311f4fa34179'},
      {'parameter_id': 'bf11768decb1d0204e2636edd05c354573d473e67f1b048369b2ee99c865bf5f',
       'attribute_id': '2e8b00e571f9d835d3f022a9ff49b9779034ab21bffdcde075d9d729fabeb960',
       'previous_attribute_id': '341769820d8937a5c9f9b980eefca37f3f37fcc6fd01c6f4c930fdb9d5dd5128'},
      {'parameter_id': 'bf11768decb1d0204e2636edd05c354573d473e67f1b048369b2ee99c865bf5f',
       'attribute_id': 'ecd93cf051988b23b3590415f4e7d550de264600d7d2af8704c973b9c98ca6a9',
       'previous_attribute_id': '341769820d8937a5c9f9b980eefca37f3f37fcc6fd01c6f4c930fdb9d5dd5128'}],
     '9a4a3ace265c9bf2facc0044ca24260c42805c6e7b2a608dfd2f56a54d9d36be': [{'parameter_id': '9a4a3ace265c9bf2facc0044ca24260c42805c6e7b2a608dfd2f56a54d9d36be',
       'attribute_id': 'fa4e8d81f4dbe6d306aff59bea4693d325a203be5d5b9fde5d5f1e7cce26b861',
       'previous_attribute_id': None},
      {'parameter_id': '9a4a3ace265c9bf2facc0044ca24260c42805c6e7b2a608dfd2f56a54d9d36be',
       'attribute_id': 'c26e7e96f0f3647c159b0934f4dc55207ac059abb56005d7a8acd8344ef14798',
       'previous_attribute_id': 'fa4e8d81f4dbe6d306aff59bea4693d325a203be5d5b9fde5d5f1e7cce26b861'},
      {'parameter_id': '9a4a3ace265c9bf2facc0044ca24260c42805c6e7b2a608dfd2f56a54d9d36be',
       'attribute_id': 'f7cd339f77c1799f399d8ebcbb27f2d41a448622254d64e9270ae2316211ac1d',
       'previous_attribute_id': 'c26e7e96f0f3647c159b0934f4dc55207ac059abb56005d7a8acd8344ef14798'},
      {'parameter_id': '9a4a3ace265c9bf2facc0044ca24260c42805c6e7b2a608dfd2f56a54d9d36be',
       'attribute_id': '15a33fe62774a1857b404f453ba1195eb4355e10bc9519f2f991dd7ba8db19b7',
       'previous_attribute_id': 'f7cd339f77c1799f399d8ebcbb27f2d41a448622254d64e9270ae2316211ac1d'},
      {'parameter_id': '9a4a3ace265c9bf2facc0044ca24260c42805c6e7b2a608dfd2f56a54d9d36be',
       'attribute_id': '99761e3d58bc213dc3ab33f2dc8dabe5f97d3aea6b59cd367d40b76937f49aa6',
       'previous_attribute_id': '15a33fe62774a1857b404f453ba1195eb4355e10bc9519f2f991dd7ba8db19b7'},
      {'parameter_id': '9a4a3ace265c9bf2facc0044ca24260c42805c6e7b2a608dfd2f56a54d9d36be',
       'attribute_id': '036a9c122c1f4c9304afa23c4d1fce5224c270a206889afa689f3efb36ff368d',
       'previous_attribute_id': '99761e3d58bc213dc3ab33f2dc8dabe5f97d3aea6b59cd367d40b76937f49aa6'},
      {'parameter_id': '9a4a3ace265c9bf2facc0044ca24260c42805c6e7b2a608dfd2f56a54d9d36be',
       'attribute_id': 'e72aa8015688052f4e7fddbf4c74e5bf2bd74239ebf3902a5fdc008ecb03aa46',
       'previous_attribute_id': '036a9c122c1f4c9304afa23c4d1fce5224c270a206889afa689f3efb36ff368d'},
      {'parameter_id': '9a4a3ace265c9bf2facc0044ca24260c42805c6e7b2a608dfd2f56a54d9d36be',
       'attribute_id': '0ae8eda3dbeedbc17e27a679c5426dd3af1434f7c37b4ecd3b2fb5c492272b75',
       'previous_attribute_id': 'e72aa8015688052f4e7fddbf4c74e5bf2bd74239ebf3902a5fdc008ecb03aa46'},
      {'parameter_id': '9a4a3ace265c9bf2facc0044ca24260c42805c6e7b2a608dfd2f56a54d9d36be',
       'attribute_id': 'cedcfbb0d95798514b6aaf30118fff7b46f863f1bc8b80bb2ddd2145e5b3f318',
       'previous_attribute_id': '0ae8eda3dbeedbc17e27a679c5426dd3af1434f7c37b4ecd3b2fb5c492272b75'}],
     'ace2f31433212fbf9e764069a30a7675ca78f496d31f061d06d0a0420fc52768': [{'parameter_id': 'ace2f31433212fbf9e764069a30a7675ca78f496d31f061d06d0a0420fc52768',
       'attribute_id': 'ace2f31433212fbf9e764069a30a7675ca78f496d31f061d06d0a0420fc52768',
       'previous_attribute_id': None}],
     '1a4f19ee9e186ee739daecbc778501c5851d3fb5d05c4a3c1200e599855e8689': [{'parameter_id': '1a4f19ee9e186ee739daecbc778501c5851d3fb5d05c4a3c1200e599855e8689',
       'attribute_id': '87d93e1862f0f58199c3fcb7114b92fe59f03581804b1c8419868fb00ff8a469',
       'previous_attribute_id': None},
      {'parameter_id': '1a4f19ee9e186ee739daecbc778501c5851d3fb5d05c4a3c1200e599855e8689',
       'attribute_id': 'b4a705d09aa0361f4db453da32abb05a5c4e0249d6180d2b8a58d72d08dbd6a0',
       'previous_attribute_id': '87d93e1862f0f58199c3fcb7114b92fe59f03581804b1c8419868fb00ff8a469'},
      {'parameter_id': '1a4f19ee9e186ee739daecbc778501c5851d3fb5d05c4a3c1200e599855e8689',
       'attribute_id': 'e4e2c33a2ea67f34bf3ac1e9d99edaad501c7dc4ea82f4b60e9d959418d8438d',
       'previous_attribute_id': 'b4a705d09aa0361f4db453da32abb05a5c4e0249d6180d2b8a58d72d08dbd6a0'},
      {'parameter_id': '1a4f19ee9e186ee739daecbc778501c5851d3fb5d05c4a3c1200e599855e8689',
       'attribute_id': '777abf12375b7f605b21535eb0d6232ce99581c6d2b1179af976cd0708ad27ff',
       'previous_attribute_id': 'e4e2c33a2ea67f34bf3ac1e9d99edaad501c7dc4ea82f4b60e9d959418d8438d'}]}



#### attribute_values


```python
pf.commited_tables['ffb2fa4d1f14786e7a11641a870c3db55f08f375fb7ac00c9a2127f7cd801a60']['attribute_values'][param_set_id]
```




    {'4cea5b09e77da310c5105978f2ceea5c5d8c9c7b65d0e00b45135ea90fc011af': [{'attribute_id': 'ee25af17445d7622cbf61a5b9424246a1f3104704b68bd31b9b7532471d492e5',
       'attribute_name': 'name',
       'attribute_value': 'Some name',
       'attribute_value_type': 'str'},
      {'attribute_id': '8b5b2be24e60ba407b90967820da8a1385a6d67691a02bc663703160ef655101',
       'attribute_name': 'age',
       'attribute_value': '111',
       'attribute_value_type': 'int'},
      {'attribute_id': '52ea872c99c586530348ba8902dcab831761673d25cf1cb0023576820289ce6b',
       'attribute_name': 'country',
       'attribute_value': 'Some land',
       'attribute_value_type': 'str'}],
     'bf11768decb1d0204e2636edd05c354573d473e67f1b048369b2ee99c865bf5f': [{'attribute_id': '7d5ee0e0cd00c3703e5f346c6887baf503faaf9fe090774f6866311f4fa34179',
       'attribute_name': 'employee',
       'attribute_value': "{'name': 'Some name', 'id': 10293, 'contact': {'email': 'some.name@example.com', 'phone': '+1234567890'}}",
       'attribute_value_type': 'dict'},
      {'attribute_id': 'ee25af17445d7622cbf61a5b9424246a1f3104704b68bd31b9b7532471d492e5',
       'attribute_name': 'name',
       'attribute_value': 'Some name',
       'attribute_value_type': 'str'},
      {'attribute_id': '3367512147bf19ae99c986b356af11dcdc067376aa1b79eb8ba8f61324e8dc18',
       'attribute_name': 'id',
       'attribute_value': '10293',
       'attribute_value_type': 'int'},
      {'attribute_id': '341769820d8937a5c9f9b980eefca37f3f37fcc6fd01c6f4c930fdb9d5dd5128',
       'attribute_name': 'contact',
       'attribute_value': "{'email': 'some.name@example.com', 'phone': '+1234567890'}",
       'attribute_value_type': 'dict'},
      {'attribute_id': '2e8b00e571f9d835d3f022a9ff49b9779034ab21bffdcde075d9d729fabeb960',
       'attribute_name': 'email',
       'attribute_value': 'some.name@example.com',
       'attribute_value_type': 'str'},
      {'attribute_id': 'ecd93cf051988b23b3590415f4e7d550de264600d7d2af8704c973b9c98ca6a9',
       'attribute_name': 'phone',
       'attribute_value': '+1234567890',
       'attribute_value_type': 'str'}],
     '9a4a3ace265c9bf2facc0044ca24260c42805c6e7b2a608dfd2f56a54d9d36be': [{'attribute_id': 'fa4e8d81f4dbe6d306aff59bea4693d325a203be5d5b9fde5d5f1e7cce26b861',
       'attribute_name': '0',
       'attribute_value': '\\X/Fc7;/v`6joU5z*n{35zFB<<6BMC,}/_04],>v$Jr2&0M_7qU\'IY#6uO\\$kEr.)Z&Bb|jUU>QU6\'tu552PTi{fEv&yZ5W[pnU@5>j9#wi9S0^23t1W,0}><v+Pv+9:~v4D_kJGRk&R@e:&UR::#"qAClD~@-%]atMP+.,m3E/x0)|?Xq/bh#FTAA$r@BG9R-yCsD1zW!KG5pZBQxKeVT\'ZX8X6C2H\\@B(h1H,MxhGc|Tcbq@T5]0x5Sb]U~Yz',
       'attribute_value_type': 'str'},
      {'attribute_id': 'c26e7e96f0f3647c159b0934f4dc55207ac059abb56005d7a8acd8344ef14798',
       'attribute_name': '1',
       'attribute_value': 'A7J+1x5|?r]2zg54nxoa>W*loh8Np~*9+*KxWLuD/Z5g!=DN>}c#]Dt->tiov?|Ms.!Hd{@%G[baAjcfSpR<iKJ^_!k+^@,uY&fER+gS%BU^X;s3>}.bKs=\\g_@)\\T5R6R{WZO^KG!j&yl.j~[<7&brDKV<rye]G{Y2_0PFVh/yoqud{2C$Z-:~4mxucBvJlm-"{Qyy|U&SY4Fw.bjFa8,62Z|he;+I\\)ggi$<rVl|9"%n]j&*PP;b!opy^=_pb',
       'attribute_value_type': 'str'},
      {'attribute_id': 'f7cd339f77c1799f399d8ebcbb27f2d41a448622254d64e9270ae2316211ac1d',
       'attribute_name': '2',
       'attribute_value': 'LUs%<HRbNA_4:yYTh!!x&oFZ201sQ7;~Q_IYr"lGRMd=xx,r}|n8zHIP6%JN)",vQIP-bV&y3V5Z6X8NbiQlA05-&g{2-(}h%oiR\\"Q1&1xed&gBtx)L]?(jP{1Bi|x=T<}-+1hxKP;[~$C=J*2LBohTMD~;v6<}&I!]XA)-qmvjON,@Ds~GZ9/PB2a&hdJE/j:ZN![gS>HO`EHTf"`x~=CD|oG.^=g?H:_.JSk5z)g,*moq_f\'A5z$+%V_~CC/',
       'attribute_value_type': 'str'},
      {'attribute_id': '15a33fe62774a1857b404f453ba1195eb4355e10bc9519f2f991dd7ba8db19b7',
       'attribute_name': '3',
       'attribute_value': 'b&z(/Z{s@U>@o!}{+(mmygo}u~AHgdu>:jz4fNBm0;Q6\'o+f%H/z3^8Hh!w<#z.~21H2]$rpWSUD\'\'cV+;hZkyVa?c8u@S.{ct3fzB/&yb]jUAC.wg=PW,va1g]/4Aq6x}Ll.yf\'L[~4ejf[/ZstFQIxU4|c_AKK!Nsf)6I?L3ZLvPzJ0+/$~V_|#9&B\\Gu03=|;5a[@TK-i#"o),hi1Q6D=F)"WNQ/O>na@^%!,iV>9kdRj`V@*Vh:}Dq%w\\r=',
       'attribute_value_type': 'str'},
      {'attribute_id': '99761e3d58bc213dc3ab33f2dc8dabe5f97d3aea6b59cd367d40b76937f49aa6',
       'attribute_name': '4',
       'attribute_value': ".#;5Cu]5~8ZmYBLI4w)|h=)C<(#`KSoM,`7n?dun7]LX>j7/U>Jf||4`AN_u*W!*3)*+<l'4alH5k5dO&`M@*&aZv(cZnr{uBla&b]8SJ1-}FRb3kj{PODJ'qB$t}[]B;%JE/Ag.i^s;1xVwBrs]a~1Y7HPn'Z<SN8Da%+zoFe|`nq$^/EDpB5srxdSc)ej`O\\C+j\\3z@?UKndHAwU{dbk?BxqSAZ@!{k2fZfNO)|JaJrr#eskY!?+:+6,tW-lv",
       'attribute_value_type': 'str'},
      {'attribute_id': '036a9c122c1f4c9304afa23c4d1fce5224c270a206889afa689f3efb36ff368d',
       'attribute_name': '5',
       'attribute_value': '0S)*}6"i)kUg3=n:}>Ji)!"BTbzsdgps8{cR]`.41QJ<O{wr[}}gGan_O63D0WBr]<zJ-`U4W{33`_Il3Z]b{jdzvK2/4^AZu1h<(,dRr.hB?#B|O"3%5MuyeOj~k8WIX1)}Ef^Lhm)Ix@&`RNyX3{)AR[n]ayEDh!dTK%vuOHC=j$Lax_dJezu^V`of@x!?(Dss=xuXD&%*;(ZA\\x2Uty)-7y,a)Q{{|QKme9sRyU\\zM?^DxNg`SG0$K:L|,cf',
       'attribute_value_type': 'str'},
      {'attribute_id': 'e72aa8015688052f4e7fddbf4c74e5bf2bd74239ebf3902a5fdc008ecb03aa46',
       'attribute_name': '6',
       'attribute_value': 'Xb;IgM/`T:VY*6XQ:nvB3)>@32w8H-cD"g>x`MlWp_TnuyCaz62e??md<8tR$Q=X7<9mC5.wHLX?;*z3-z\\v,\'uINGC)x%~3Jz^4P~?|KLTlENtt,d4#<eM<7]M[7}&G1"u1gELm^{.Bn\\jLfrPh?o.R1g8L*jiiwia-WClq`;a/..62oEl}6.8u7+M}P(#2UI>{^IJwo4\'C,@FqjvO~H2iktlg],d*I3?z"j9>$.~(\\04NHsj\'TsJ_Cu1Qs-c\\',
       'attribute_value_type': 'str'},
      {'attribute_id': '0ae8eda3dbeedbc17e27a679c5426dd3af1434f7c37b4ecd3b2fb5c492272b75',
       'attribute_name': '7',
       'attribute_value': 'pq.%\\nmm;M!^cyS|ApMpnjUS<#Ov?e+n"wX/to.wjifCG.fKK@6gI+Wvax&}j18R8p!xB}BIHgkG|f]$%Wi%;#8JP$rzo"XYnga+j7=])2}`;nR}#7cx\'$1EFq-.iMC/Z|"<;wO<}2#,IM\'Mr\\3&]}bZ6DKFdLH>W9G@E}A6M}!FQD]nCPMuh^G9Z+]{R8)LZXE,l+xA~\'h(nK>ZxwJ5L=!I9iHlB;bM!G[Snh,YsZxf4v,t!*QhgB^1p9D1\\c-',
       'attribute_value_type': 'str'},
      {'attribute_id': 'cedcfbb0d95798514b6aaf30118fff7b46f863f1bc8b80bb2ddd2145e5b3f318',
       'attribute_name': '8',
       'attribute_value': '+-;Zt=ex',
       'attribute_value_type': 'str'}],
     'ace2f31433212fbf9e764069a30a7675ca78f496d31f061d06d0a0420fc52768': [{'attribute_id': 'ace2f31433212fbf9e764069a30a7675ca78f496d31f061d06d0a0420fc52768',
       'attribute_name': '0',
       'attribute_value': "b'\\x80\\x04\\x95h\\x00\\x00\\x00\\x00\\x00\\x00\\x00}\\x94(\\x8c\\x07integer\\x94K*\\x8c\\x05float\\x94G@\\t!\\xf9\\xf0\\x1b\\x86n\\x8c\\x06string\\x94\\x8c\\rHello, world!\\x94\\x8c\\x04list\\x94]\\x94(K\\x01K\\x02K\\x03K\\x04K\\x05e\\x8c\\x04dict\\x94}\\x94\\x8c\\x03key\\x94\\x8c\\x05value\\x94su.'",
       'attribute_value_type': 'bytes'}],
     '1a4f19ee9e186ee739daecbc778501c5851d3fb5d05c4a3c1200e599855e8689': [{'attribute_id': '87d93e1862f0f58199c3fcb7114b92fe59f03581804b1c8419868fb00ff8a469',
       'attribute_name': '0',
       'attribute_value': 'b\'{\\n "cells": [\\n  {\\n   "cell_type": "markdown",\\n   "metadata": {},\\n   "source": [\\n    "### Example ipynb file"\\n   ]\\n  },\\n  {\\n   "cell_type": "code",\\n   "execution_count": 1,\\n   "metadata": {},\\n   "outputs": [\\n    {\\n     "data": {\\n      "te',
       'attribute_value_type': 'bytes'},
      {'attribute_id': 'b4a705d09aa0361f4db453da32abb05a5c4e0249d6180d2b8a58d72d08dbd6a0',
       'attribute_name': '1',
       'attribute_value': 'xt/plain": [\\n       "4"\\n      ]\\n     },\\n     "execution_count": 1,\\n     "metadata": {},\\n     "output_type": "execute_result"\\n    }\\n   ],\\n   "source": [\\n    "2+2"\\n   ]\\n  }\\n ],\\n "metadata": {\\n  "kernelspec": {\\n   "display_name": "testenv",\\n',
       'attribute_value_type': 'bytes'},
      {'attribute_id': 'e4e2c33a2ea67f34bf3ac1e9d99edaad501c7dc4ea82f4b60e9d959418d8438d',
       'attribute_name': '2',
       'attribute_value': '   "language": "python",\\n   "name": "python3"\\n  },\\n  "language_info": {\\n   "codemirror_mode": {\\n    "name": "ipython",\\n    "version": 3\\n   },\\n   "file_extension": ".py",\\n   "mimetype": "text/x-python",\\n   "name": "python",\\n   "nbconvert_exporte',
       'attribute_value_type': 'bytes'},
      {'attribute_id': '777abf12375b7f605b21535eb0d6232ce99581c6d2b1179af976cd0708ad27ff',
       'attribute_name': '3',
       'attribute_value': 'r": "python",\\n   "pygments_lexer": "ipython3",\\n   "version": "3.9.15"\\n  }\\n },\\n "nbformat": 4,\\n "nbformat_minor": 2\\n}\\n\'',
       'attribute_value_type': 'bytes'}]}




```python
pd.DataFrame([tab for param_id, tab_list in pf.commited_tables['ffb2fa4d1f14786e7a11641a870c3db55f08f375fb7ac00c9a2127f7cd801a60']\
    ['attribute_values']\
        [param_set_id].items() \
            for tab in tab_list])
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
      <th>attribute_id</th>
      <th>attribute_name</th>
      <th>attribute_value</th>
      <th>attribute_value_type</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>ee25af17445d7622cbf61a5b9424246a1f3104704b68bd...</td>
      <td>name</td>
      <td>Some name</td>
      <td>str</td>
    </tr>
    <tr>
      <th>1</th>
      <td>8b5b2be24e60ba407b90967820da8a1385a6d67691a02b...</td>
      <td>age</td>
      <td>111</td>
      <td>int</td>
    </tr>
    <tr>
      <th>2</th>
      <td>52ea872c99c586530348ba8902dcab831761673d25cf1c...</td>
      <td>country</td>
      <td>Some land</td>
      <td>str</td>
    </tr>
    <tr>
      <th>3</th>
      <td>7d5ee0e0cd00c3703e5f346c6887baf503faaf9fe09077...</td>
      <td>employee</td>
      <td>{'name': 'Some name', 'id': 10293, 'contact': ...</td>
      <td>dict</td>
    </tr>
    <tr>
      <th>4</th>
      <td>ee25af17445d7622cbf61a5b9424246a1f3104704b68bd...</td>
      <td>name</td>
      <td>Some name</td>
      <td>str</td>
    </tr>
    <tr>
      <th>5</th>
      <td>3367512147bf19ae99c986b356af11dcdc067376aa1b79...</td>
      <td>id</td>
      <td>10293</td>
      <td>int</td>
    </tr>
    <tr>
      <th>6</th>
      <td>341769820d8937a5c9f9b980eefca37f3f37fcc6fd01c6...</td>
      <td>contact</td>
      <td>{'email': 'some.name@example.com', 'phone': '+...</td>
      <td>dict</td>
    </tr>
    <tr>
      <th>7</th>
      <td>2e8b00e571f9d835d3f022a9ff49b9779034ab21bffdcd...</td>
      <td>email</td>
      <td>some.name@example.com</td>
      <td>str</td>
    </tr>
    <tr>
      <th>8</th>
      <td>ecd93cf051988b23b3590415f4e7d550de264600d7d2af...</td>
      <td>phone</td>
      <td>+1234567890</td>
      <td>str</td>
    </tr>
    <tr>
      <th>9</th>
      <td>fa4e8d81f4dbe6d306aff59bea4693d325a203be5d5b9f...</td>
      <td>0</td>
      <td>\X/Fc7;/v`6joU5z*n{35zFB&lt;&lt;6BMC,}/_04],&gt;v$Jr2&amp;0...</td>
      <td>str</td>
    </tr>
    <tr>
      <th>10</th>
      <td>c26e7e96f0f3647c159b0934f4dc55207ac059abb56005...</td>
      <td>1</td>
      <td>A7J+1x5|?r]2zg54nxoa&gt;W*loh8Np~*9+*KxWLuD/Z5g!=...</td>
      <td>str</td>
    </tr>
    <tr>
      <th>11</th>
      <td>f7cd339f77c1799f399d8ebcbb27f2d41a448622254d64...</td>
      <td>2</td>
      <td>LUs%&lt;HRbNA_4:yYTh!!x&amp;oFZ201sQ7;~Q_IYr"lGRMd=xx...</td>
      <td>str</td>
    </tr>
    <tr>
      <th>12</th>
      <td>15a33fe62774a1857b404f453ba1195eb4355e10bc9519...</td>
      <td>3</td>
      <td>b&amp;z(/Z{s@U&gt;@o!}{+(mmygo}u~AHgdu&gt;:jz4fNBm0;Q6'o...</td>
      <td>str</td>
    </tr>
    <tr>
      <th>13</th>
      <td>99761e3d58bc213dc3ab33f2dc8dabe5f97d3aea6b59cd...</td>
      <td>4</td>
      <td>.#;5Cu]5~8ZmYBLI4w)|h=)C&lt;(#`KSoM,`7n?dun7]LX&gt;j...</td>
      <td>str</td>
    </tr>
    <tr>
      <th>14</th>
      <td>036a9c122c1f4c9304afa23c4d1fce5224c270a206889a...</td>
      <td>5</td>
      <td>0S)*}6"i)kUg3=n:}&gt;Ji)!"BTbzsdgps8{cR]`.41QJ&lt;O{...</td>
      <td>str</td>
    </tr>
    <tr>
      <th>15</th>
      <td>e72aa8015688052f4e7fddbf4c74e5bf2bd74239ebf390...</td>
      <td>6</td>
      <td>Xb;IgM/`T:VY*6XQ:nvB3)&gt;@32w8H-cD"g&gt;x`MlWp_Tnuy...</td>
      <td>str</td>
    </tr>
    <tr>
      <th>16</th>
      <td>0ae8eda3dbeedbc17e27a679c5426dd3af1434f7c37b4e...</td>
      <td>7</td>
      <td>pq.%\nmm;M!^cyS|ApMpnjUS&lt;#Ov?e+n"wX/to.wjifCG....</td>
      <td>str</td>
    </tr>
    <tr>
      <th>17</th>
      <td>cedcfbb0d95798514b6aaf30118fff7b46f863f1bc8b80...</td>
      <td>8</td>
      <td>+-;Zt=ex</td>
      <td>str</td>
    </tr>
    <tr>
      <th>18</th>
      <td>ace2f31433212fbf9e764069a30a7675ca78f496d31f06...</td>
      <td>0</td>
      <td>b'\x80\x04\x95h\x00\x00\x00\x00\x00\x00\x00}\x...</td>
      <td>bytes</td>
    </tr>
    <tr>
      <th>19</th>
      <td>87d93e1862f0f58199c3fcb7114b92fe59f03581804b1c...</td>
      <td>0</td>
      <td>b'{\n "cells": [\n  {\n   "cell_type": "markdo...</td>
      <td>bytes</td>
    </tr>
    <tr>
      <th>20</th>
      <td>b4a705d09aa0361f4db453da32abb05a5c4e0249d6180d...</td>
      <td>1</td>
      <td>xt/plain": [\n       "4"\n      ]\n     },\n  ...</td>
      <td>bytes</td>
    </tr>
    <tr>
      <th>21</th>
      <td>e4e2c33a2ea67f34bf3ac1e9d99edaad501c7dc4ea82f4...</td>
      <td>2</td>
      <td>"language": "python",\n   "name": "python3"...</td>
      <td>bytes</td>
    </tr>
    <tr>
      <th>22</th>
      <td>777abf12375b7f605b21535eb0d6232ce99581c6d2b117...</td>
      <td>3</td>
      <td>r": "python",\n   "pygments_lexer": "ipython3"...</td>
      <td>bytes</td>
    </tr>
  </tbody>
</table>
</div>



### 4. Pushing solutions with DatabaseConnector


```python
pf.push_solution(solution_id='ffb2fa4d1f14786e7a11641a870c3db55f08f375fb7ac00c9a2127f7cd801a60',
                 parameter_set_ids=['a54f04d2ff154294309403206e059aec556cdcfa51120649ce663f3230a970d5'])
```

    HTTP Request: POST http://localhost:8000/insert "HTTP/1.1 200 OK"





    True



### 5. Pulling solution with DatabaseConnector


```python
params_path = "../tests/parameterframe/example_configs"

pf2 = ParameterFrame(
    params_path = params_path
)

pf2.pull_solution(solution_id='ffb2fa4d1f14786e7a11641a870c3db55f08f375fb7ac00c9a2127f7cd801a60',
                 parameter_set_id='a54f04d2ff154294309403206e059aec556cdcfa51120649ce663f3230a970d5')
```

    HTTP Request: POST http://localhost:8000/search "HTTP/1.1 200 OK"
    HTTP Request: POST http://localhost:8000/search "HTTP/1.1 200 OK"
    HTTP Request: POST http://localhost:8000/search "HTTP/1.1 200 OK"


### 6. Reconstructing files


```python
os.listdir("../tests/parameterframe/reconstructed_files")
```




    ['.gitignore']




```python
pf2.reconstruct_parameter_set(
    solution_name = "example_solution",
    parameter_set_name = "test_set",
    params_path = "../tests/parameterframe/reconstructed_files"
)
```


```python
os.listdir("../tests/parameterframe/reconstructed_files")
```




    ['param_2.yaml',
     'param_11.dill',
     '.gitignore',
     'param_1.yaml',
     'param_10.txt',
     'param_21.ipynb']


