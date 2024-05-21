# Parameterframe

The module provides an interface for managing solution parameters.
It allows for the structured storage and retrieval of parameter sets from a database.



```python
import sys
import pandas as pd
import os
sys.path.append('../')
from parameterframe import ParameterFrame, MockerDatabaseConnector, SqlAlchemyDatabaseManager

```

## Content

1. Adding new solution and uploading it
2. Processing new files and creating parameter set
3. Adding parameter set to solution and commiting
4. Uploading parameter sets
5. Getting latest parameter set id for solution
6. Changing parameter set status
7. Pulling select parameter sets
8. Reconstructing parameter se
9. Structure of local commit tables
10. Scores

### 1. Adding new solution and uploading it


```python
# - with database connector for MockerDB
pf = ParameterFrame(
    database_connector = MockerDatabaseConnector(connection_details = {
    'base_url' : 'http://localhost:8001'})
)
```

when using SqlAlchemyDatabaseManager with database for the first time, it might be useful to create tables with `SqlAlchemyDatabaseManager.create_tables` and if schema of the database needs to be reset `SqlAlchemyDatabaseManager.drop_tables`


```python
# - with SqlAlchemy database connector
pf = ParameterFrame(
    database_connector = SqlAlchemyDatabaseManager(connection_details = {
    'base_url' : 'postgresql+psycopg2://postgres:mysecretpassword@localhost:5432/mytestdb'})
)
```


```python
pf.show_solutions()
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
      <th>deprecation_date</th>
      <th>maintainers</th>
      <th>commited_parameter_sets</th>
      <th>aos</th>
      <th>pos</th>
    </tr>
  </thead>
  <tbody>
  </tbody>
</table>
</div>




```python
pf.add_solution(
    # mandatory
    solution_name="new_example_solution",
    # optional description
    solution_description="Description of new example solution.",
    deployment_date="2024-xx-xx",
    deprecation_date=None,
    maintainers="some text about maintainers credentials"
)

pf.add_solution(
    # mandatory
    solution_name="new_example_solution2",
    # optional description
    solution_description="Description of new example solution.",
    deployment_date="2024-xx-xx",
    deprecation_date=None,
    maintainers="some text about maintainers credentials"
)
```

    Solution id for new_example_solution: b5c2e4a9bdcb57cc70bdb7310c7909cc1549550add79e3fbcc8aa1cf323cd8ca
    Solution id for new_example_solution2: 1c0b910dc0074ea3966fbb1a96038e5eaee8dc1b873f9867830e0659b54dd311





    True




```python
pf.commit_solution(
    # either solution id or solution name should be provided
    solution_name="new_example_solution"
)

pf.commit_solution(
    # either solution id or solution name should be provided
    solution_name="new_example_solution2"
)
```

    Commited solution description for b5c2e4a9bdcb57cc70bdb7310c7909cc1549550add79e3fbcc8aa1cf323cd8ca
    Commited solution description for 1c0b910dc0074ea3966fbb1a96038e5eaee8dc1b873f9867830e0659b54dd311





    True




```python
pf.show_solutions()
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
      <th>deprecation_date</th>
      <th>maintainers</th>
      <th>commited_parameter_sets</th>
      <th>aos</th>
      <th>pos</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>b5c2e4a9bdcb57cc70bdb7310c7909cc1549550add79e3fbcc8aa1cf323cd8ca</td>
      <td>new_example_solution</td>
      <td>Description of new example solution.</td>
      <td>2024-xx-xx</td>
      <td>None</td>
      <td>some text about maintainers credentials</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>1</th>
      <td>1c0b910dc0074ea3966fbb1a96038e5eaee8dc1b873f9867830e0659b54dd311</td>
      <td>new_example_solution2</td>
      <td>Description of new example solution.</td>
      <td>2024-xx-xx</td>
      <td>None</td>
      <td>some text about maintainers credentials</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
  </tbody>
</table>
</div>




```python
pf.push_solution(
    # either solution id or solution name should be provided
    solution_name = "new_example_solution"
)
```




    True



### 2. Processing new files and creating parameter set


```python
params_path = "../tests/parameterframe/example_configs"
```


```python
pf = ParameterFrame(
    params_path = params_path,
    database_connector = MockerDatabaseConnector(connection_details = {
    'base_url' : 'http://localhost:8001'})
)
```


```python
pf = ParameterFrame(
    params_path = params_path,
    database_connector = SqlAlchemyDatabaseManager(connection_details = {
    'base_url' : 'postgresql+psycopg2://postgres:mysecretpassword@localhost:5432/mytestdb'})
)
```


```python
pf.process_parameters_from_files()
```




    True




```python
pf.show_solutions()
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
      <th>deprecation_date</th>
      <th>maintainers</th>
      <th>commited_parameter_sets</th>
      <th>aos</th>
      <th>pos</th>
    </tr>
  </thead>
  <tbody>
  </tbody>
</table>
</div>




```python
pf.make_parameter_set(
    parameter_set_name="test_set",
    parameter_set_description="example parameters for test purposes",
    parameter_names=['param_1','param_2','param_10', 'param_11','param_21']
)
```

    Parameter set id for test_set: a54f04d2ff154294309403206e059aec556cdcfa51120649ce663f3230a970d5


### 3. Adding parameter set to solution and commiting


```python
pf.add_parameter_set_to_solution(
    solution_id = 'b5c2e4a9bdcb57cc70bdb7310c7909cc1549550add79e3fbcc8aa1cf323cd8ca',
    parameter_set_name="test_set")
```

    b5c2e4a9bdcb57cc70bdb7310c7909cc1549550add79e3fbcc8aa1cf323cd8ca is not in solutions saved to memory!
    Name pink_happy_car_642 is assigned to b5c2e4a9bdcb57cc70bdb7310c7909cc1549550add79e3fbcc8aa1cf323cd8ca temporarily!





    True




```python
pf.commit_solution(solution_name="pink_happy_car_642",
                    parameter_set_names=["test_set"])
```

    Commited solution tables for b5c2e4a9bdcb57cc70bdb7310c7909cc1549550add79e3fbcc8aa1cf323cd8ca





    True




```python
pf.show_solutions()
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
      <th>deprecation_date</th>
      <th>maintainers</th>
      <th>commited_parameter_sets</th>
      <th>aos</th>
      <th>pos</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>b5c2e4a9bdcb57cc70bdb7310c7909cc1549550add79e3fbcc8aa1cf323cd8ca</td>
      <td>None</td>
      <td>None</td>
      <td>None</td>
      <td>None</td>
      <td>None</td>
      <td>1</td>
      <td>0.05</td>
      <td>0.0</td>
    </tr>
  </tbody>
</table>
</div>




```python
pf.show_parameter_sets(solution_id = 'b5c2e4a9bdcb57cc70bdb7310c7909cc1549550add79e3fbcc8aa1cf323cd8ca')
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
      <th>deployment_status</th>
      <th>insertion_datetime</th>
      <th>commited_parameters</th>
      <th>aos</th>
      <th>pos</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>a54f04d2ff154294309403206e059aec556cdcfa51120649ce663f3230a970d5</td>
      <td>test_set</td>
      <td>example parameters for test purposes</td>
      <td>STAGING</td>
      <td>2024-05-21 03:03:23</td>
      <td>5</td>
      <td>0.05</td>
      <td>0.0</td>
    </tr>
  </tbody>
</table>
</div>




```python
pf.show_parameters(solution_id = 'b5c2e4a9bdcb57cc70bdb7310c7909cc1549550add79e3fbcc8aa1cf323cd8ca',
                   parameter_set_id = 'a54f04d2ff154294309403206e059aec556cdcfa51120649ce663f3230a970d5')
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
      <th>commited_attributes</th>
      <th>aos</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>4cea5b09e77da310c5105978f2ceea5c5d8c9c7b65d0e00b45135ea90fc011af</td>
      <td>param_1</td>
      <td></td>
      <td>param_1.yaml</td>
      <td>yaml</td>
      <td>3</td>
      <td>0.05</td>
    </tr>
    <tr>
      <th>1</th>
      <td>bf11768decb1d0204e2636edd05c354573d473e67f1b048369b2ee99c865bf5f</td>
      <td>param_2</td>
      <td></td>
      <td>param_2.yaml</td>
      <td>yaml</td>
      <td>6</td>
      <td>0.05</td>
    </tr>
    <tr>
      <th>2</th>
      <td>9a4a3ace265c9bf2facc0044ca24260c42805c6e7b2a608dfd2f56a54d9d36be</td>
      <td>param_10</td>
      <td></td>
      <td>param_10.txt</td>
      <td>txt</td>
      <td>9</td>
      <td>0.00</td>
    </tr>
    <tr>
      <th>3</th>
      <td>ace2f31433212fbf9e764069a30a7675ca78f496d31f061d06d0a0420fc52768</td>
      <td>param_11</td>
      <td></td>
      <td>param_11.dill</td>
      <td>other</td>
      <td>1</td>
      <td>0.00</td>
    </tr>
    <tr>
      <th>4</th>
      <td>1a4f19ee9e186ee739daecbc778501c5851d3fb5d05c4a3c1200e599855e8689</td>
      <td>param_21</td>
      <td></td>
      <td>param_21.ipynb</td>
      <td>other</td>
      <td>2</td>
      <td>0.00</td>
    </tr>
  </tbody>
</table>
</div>



### 4. Uploading parameter sets


```python
pf.push_solution(solution_id='b5c2e4a9bdcb57cc70bdb7310c7909cc1549550add79e3fbcc8aa1cf323cd8ca',
                 parameter_set_names=["test_set"])
```




    True



### 5. Getting latest parameter set id for solution


```python
# - with database connector for MockerDB
pf = ParameterFrame(
    database_connector = MockerDatabaseConnector(connection_details = {
    'base_url' : 'http://localhost:8001'})
)
```


```python
# - with SqlAlchemy database connector
pf = ParameterFrame(
    database_connector = SqlAlchemyDatabaseManager(connection_details = {
    'base_url' : 'postgresql+psycopg2://postgres:mysecretpassword@localhost:5432/mytestdb'})
)
```


```python
pf.get_parameter_set_id_for_solution(solution_id='b5c2e4a9bdcb57cc70bdb7310c7909cc1549550add79e3fbcc8aa1cf323cd8ca',
                                                        deployment_status="STAGING")
```




    ['a54f04d2ff154294309403206e059aec556cdcfa51120649ce663f3230a970d5']




```python
pf.get_deployment_status(solution_id='b5c2e4a9bdcb57cc70bdb7310c7909cc1549550add79e3fbcc8aa1cf323cd8ca',
                         parameter_set_id='a54f04d2ff154294309403206e059aec556cdcfa51120649ce663f3230a970d5')
```




    'STAGING'



### 6. Changing parameter set status


```python
# - with database connector for MockerDB
pf = ParameterFrame(
    database_connector = MockerDatabaseConnector(connection_details = {
    'base_url' : 'http://localhost:8001'})
)
```


```python
# - with SqlAlchemy database connector
pf = ParameterFrame(
    database_connector = SqlAlchemyDatabaseManager(connection_details = {
    'base_url' : 'postgresql+psycopg2://postgres:mysecretpassword@localhost:5432/mytestdb'})
)
```


```python
pf.database_connector.modify_parameter_set_status(
    solution_id='b5c2e4a9bdcb57cc70bdb7310c7909cc1549550add79e3fbcc8aa1cf323cd8ca',
    parameter_set_ids = 'a54f04d2ff154294309403206e059aec556cdcfa51120649ce663f3230a970d5',
    current_deployment_status = "PRODUCTION",
    new_deployment_status = "STAGING"
)
```




    True




```python
pf.change_status_from_staging_to_production(
    solution_id='b5c2e4a9bdcb57cc70bdb7310c7909cc1549550add79e3fbcc8aa1cf323cd8ca',
    parameter_set_id='a54f04d2ff154294309403206e059aec556cdcfa51120649ce663f3230a970d5'
)
```

    b5c2e4a9bdcb57cc70bdb7310c7909cc1549550add79e3fbcc8aa1cf323cd8ca + a54f04d2ff154294309403206e059aec556cdcfa51120649ce663f3230a970d5 : STAGING -> PRODUCTION



```python
pf.get_deployment_status(solution_id='b5c2e4a9bdcb57cc70bdb7310c7909cc1549550add79e3fbcc8aa1cf323cd8ca',
                         parameter_set_id='a54f04d2ff154294309403206e059aec556cdcfa51120649ce663f3230a970d5')
```




    'PRODUCTION'




```python
pf.change_status_from_production_to_archived(
    solution_id='b5c2e4a9bdcb57cc70bdb7310c7909cc1549550add79e3fbcc8aa1cf323cd8ca',
    parameter_set_id='a54f04d2ff154294309403206e059aec556cdcfa51120649ce663f3230a970d5'
)
```

    b5c2e4a9bdcb57cc70bdb7310c7909cc1549550add79e3fbcc8aa1cf323cd8ca + a54f04d2ff154294309403206e059aec556cdcfa51120649ce663f3230a970d5 : PRODUCTION -> ARCHIVED



```python
pf.get_deployment_status(solution_id='b5c2e4a9bdcb57cc70bdb7310c7909cc1549550add79e3fbcc8aa1cf323cd8ca',
                         parameter_set_id='a54f04d2ff154294309403206e059aec556cdcfa51120649ce663f3230a970d5')
```




    'ARCHIVED'




```python
pf.change_status_from_archived_production(
    solution_id='b5c2e4a9bdcb57cc70bdb7310c7909cc1549550add79e3fbcc8aa1cf323cd8ca',
    parameter_set_id='a54f04d2ff154294309403206e059aec556cdcfa51120649ce663f3230a970d5'
)
```

    No deployed parameter_set_ids with PRODUCTION from selected!
    b5c2e4a9bdcb57cc70bdb7310c7909cc1549550add79e3fbcc8aa1cf323cd8ca + a54f04d2ff154294309403206e059aec556cdcfa51120649ce663f3230a970d5 : ARCHIVED -> PRODUCTION



```python
pf.get_deployment_status(solution_id='b5c2e4a9bdcb57cc70bdb7310c7909cc1549550add79e3fbcc8aa1cf323cd8ca',
                         parameter_set_id='a54f04d2ff154294309403206e059aec556cdcfa51120649ce663f3230a970d5')
```




    'PRODUCTION'



### 7. Pulling select parameter sets


```python
params_path = "../tests/parameterframe/example_configs"
```


```python
# - with database connector for MockerDB
pf2 = ParameterFrame(
    params_path = params_path,
    database_connector = MockerDatabaseConnector(connection_details = {
    'base_url' : 'http://localhost:8001'})
)
```


```python
# - with SqlAlchemy database connector
pf2 = ParameterFrame(
    params_path = params_path,
    database_connector = SqlAlchemyDatabaseManager(connection_details = {
    'base_url' : 'postgresql+psycopg2://postgres:mysecretpassword@localhost:5432/mytestdb'})
)
```


```python
pf2.show_solutions()
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
      <th>deprecation_date</th>
      <th>maintainers</th>
      <th>commited_parameter_sets</th>
      <th>aos</th>
      <th>pos</th>
    </tr>
  </thead>
  <tbody>
  </tbody>
</table>
</div>



When pulling information with database handler, one could pull specific parameter sets, solutions and everything.


```python
pf2.pull_solution(solution_id='b5c2e4a9bdcb57cc70bdb7310c7909cc1549550add79e3fbcc8aa1cf323cd8ca',
                  # optionally specify parameter_set_id
                 parameter_set_id='a54f04d2ff154294309403206e059aec556cdcfa51120649ce663f3230a970d5')
```

    HTTP Request: POST http://localhost:8001/search "HTTP/1.1 200 OK"
    HTTP Request: POST http://localhost:8001/search "HTTP/1.1 200 OK"
    HTTP Request: POST http://localhost:8001/search "HTTP/1.1 200 OK"
    No data was found with applied filters!
    No solutions with b5c2e4a9bdcb57cc70bdb7310c7909cc1549550add79e3fbcc8aa1cf323cd8ca could be pulled!





    True




```python
pf2.pull_solution(solution_id='b5c2e4a9bdcb57cc70bdb7310c7909cc1549550add79e3fbcc8aa1cf323cd8ca',
                  # optionally specify parameter_set_id
                 parameter_set_id=None)
```

    No solutions with b5c2e4a9bdcb57cc70bdb7310c7909cc1549550add79e3fbcc8aa1cf323cd8ca could be pulled!
    No parameter sets were pulled for solution_id b5c2e4a9bdcb57cc70bdb7310c7909cc1549550add79e3fbcc8aa1cf323cd8ca
    Nothing was pulled for b5c2e4a9bdcb57cc70bdb7310c7909cc1549550add79e3fbcc8aa1cf323cd8ca





    True




```python
pf2.pull_solution(
    # optional parameter to skip pull of attributes if data pulled just for show_ methods
    pull_attribute_values = False
)
```




    True




```python
pf2.show_solutions()
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
      <th>deprecation_date</th>
      <th>maintainers</th>
      <th>commited_parameter_sets</th>
      <th>aos</th>
      <th>pos</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>cec89c4cbb8c891d388407ea93d84a5cd4f996af6d5c1b0cc5fe1cb12101acf5</td>
      <td>new_example_solution</td>
      <td>Description of new example solution.</td>
      <td>2024-xx-xx</td>
      <td>None</td>
      <td>some text about maintainers credentials</td>
      <td>6</td>
      <td>0.397157</td>
      <td>0.428571</td>
    </tr>
  </tbody>
</table>
</div>




```python
pf2.show_parameter_sets(solution_id='cec89c4cbb8c891d388407ea93d84a5cd4f996af6d5c1b0cc5fe1cb12101acf5')
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
      <th>deployment_status</th>
      <th>insertion_datetime</th>
      <th>commited_parameters</th>
      <th>aos</th>
      <th>pos</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>5779bbf896ebb8f09a6ea252b09f8adb1a416e8780cf1424fb9bb93dbec8deb5</td>
      <td>green_tiny_car_749</td>
      <td></td>
      <td>STAGING</td>
      <td>2024-05-15 01:36:09</td>
      <td>3</td>
      <td>0.025744</td>
      <td>0.285714</td>
    </tr>
    <tr>
      <th>1</th>
      <td>73ece98c90d4e0bcce8b523a8e8d2bd4290c68f2a783ea279b39fe4507e42de7</td>
      <td>blue_fuzzy_refrigerator_297</td>
      <td></td>
      <td>STAGING</td>
      <td>2024-05-15 23:57:17</td>
      <td>1</td>
      <td>0.000000</td>
      <td>0.000000</td>
    </tr>
    <tr>
      <th>2</th>
      <td>82b8c5340454adf83667e59092fedbee28213475fd58ab6b3d95b4fc60f4d45f</td>
      <td>purple_giant_television_135</td>
      <td></td>
      <td>STAGING</td>
      <td>2024-05-16 00:05:43</td>
      <td>1</td>
      <td>0.371413</td>
      <td>0.142857</td>
    </tr>
    <tr>
      <th>3</th>
      <td>3940d6dd4c0d817625a31141874c54cf0c8d88b24994f7915deb4096b3c8d0cf</td>
      <td>blue_tiny_television_381</td>
      <td></td>
      <td>STAGING</td>
      <td>2024-05-15 00:37:50</td>
      <td>2</td>
      <td>0.025744</td>
      <td>0.285714</td>
    </tr>
    <tr>
      <th>4</th>
      <td>dddc057bc151de9f8fb8caa834c8e13b789cf68cb53299b4c65c23f1e1310acd</td>
      <td>red_sad_scooter_769</td>
      <td></td>
      <td>STAGING</td>
      <td>2024-05-16 00:08:21</td>
      <td>2</td>
      <td>0.371413</td>
      <td>0.142857</td>
    </tr>
    <tr>
      <th>5</th>
      <td>2f3ee8e19d91a89298d40984df5e7bdd1f1a48008b2e61c88a7f6f81b4ab23f5</td>
      <td>silver_happy_car_441</td>
      <td></td>
      <td>STAGING</td>
      <td>2024-05-16 00:03:25</td>
      <td>1</td>
      <td>0.000000</td>
      <td>0.000000</td>
    </tr>
  </tbody>
</table>
</div>




```python
pf2.show_parameters(solution_id='cec89c4cbb8c891d388407ea93d84a5cd4f996af6d5c1b0cc5fe1cb12101acf5',
                    parameter_set_id='3940d6dd4c0d817625a31141874c54cf0c8d88b24994f7915deb4096b3c8d0cf')
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
      <th>commited_attributes</th>
      <th>aos</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>3386ebc962b1c57745ca24320bf873df6eb84a2b9cb733607d72006347bf95b8</td>
      <td>Screenshot 2024-05-04 at 02</td>
      <td></td>
      <td>Screenshot 2024-05-04 at 02.59.31.png</td>
      <td>other</td>
      <td>35</td>
      <td>0.0</td>
    </tr>
    <tr>
      <th>1</th>
      <td>5afae3951544cd3736685a3b2daa31c00106191a799b96b0c636cd35e9a416ff</td>
      <td>uploads</td>
      <td></td>
      <td>uploads.zip</td>
      <td>other</td>
      <td>61</td>
      <td>0.0</td>
    </tr>
  </tbody>
</table>
</div>




```python
pf2.show_parameters(solution_id='cec89c4cbb8c891d388407ea93d84a5cd4f996af6d5c1b0cc5fe1cb12101acf5',
                    parameter_set_id='5779bbf896ebb8f09a6ea252b09f8adb1a416e8780cf1424fb9bb93dbec8deb5')
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
      <th>commited_attributes</th>
      <th>aos</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>3386ebc962b1c57745ca24320bf873df6eb84a2b9cb733607d72006347bf95b8</td>
      <td>Screenshot 2024-05-04 at 02</td>
      <td></td>
      <td>Screenshot 2024-05-04 at 02.59.31.png</td>
      <td>other</td>
      <td>35</td>
      <td>0.0</td>
    </tr>
    <tr>
      <th>1</th>
      <td>4d8ca206d9bd09296b69a95f0c3c62d233282025964c356811510cc074cc2c49</td>
      <td>1</td>
      <td></td>
      <td>1. AF - opis projektu.pdf</td>
      <td>other</td>
      <td>34</td>
      <td>0.0</td>
    </tr>
    <tr>
      <th>2</th>
      <td>5afae3951544cd3736685a3b2daa31c00106191a799b96b0c636cd35e9a416ff</td>
      <td>uploads</td>
      <td></td>
      <td>uploads.zip</td>
      <td>other</td>
      <td>61</td>
      <td>0.0</td>
    </tr>
  </tbody>
</table>
</div>




```python
pf2.show_parameters(solution_id='cec89c4cbb8c891d388407ea93d84a5cd4f996af6d5c1b0cc5fe1cb12101acf5',
                    parameter_set_id='dddc057bc151de9f8fb8caa834c8e13b789cf68cb53299b4c65c23f1e1310acd')
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
      <th>commited_attributes</th>
      <th>aos</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>e6ae9d10f3b4d69c1ef6ff8038d13e9f0b093fc3710f2fed0259204aac2fcba4</td>
      <td>Geekbench 6</td>
      <td></td>
      <td>Geekbench 6.app.zip</td>
      <td>other</td>
      <td>1385</td>
      <td>0.0</td>
    </tr>
    <tr>
      <th>1</th>
      <td>be0886c2f5d24aa5672bf84e355d9d4adb527a36e5e973413c555200d7f3fdb2</td>
      <td>Ollama</td>
      <td></td>
      <td>Ollama.app.zip</td>
      <td>other</td>
      <td>1400</td>
      <td>0.0</td>
    </tr>
  </tbody>
</table>
</div>




```python
pf2.show_parameters(solution_id='cec89c4cbb8c891d388407ea93d84a5cd4f996af6d5c1b0cc5fe1cb12101acf5',
                    parameter_set_id='82b8c5340454adf83667e59092fedbee28213475fd58ab6b3d95b4fc60f4d45f')
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
      <th>commited_attributes</th>
      <th>aos</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>e6ae9d10f3b4d69c1ef6ff8038d13e9f0b093fc3710f2fed0259204aac2fcba4</td>
      <td>Geekbench 6</td>
      <td></td>
      <td>Geekbench 6.app.zip</td>
      <td>other</td>
      <td>1385</td>
      <td>0.0</td>
    </tr>
  </tbody>
</table>
</div>



### 8. Reconstructing parameter set


```python
os.listdir("../tests/parameterframe/reconstructed_files")
```




    []




```python
pf2.reconstruct_parameter_set(
    solution_name = "new_example_solution",
    parameter_set_name = "test_set",
    params_path = "../tests/parameterframe/reconstructed_files"
)

os.listdir("../tests/parameterframe/reconstructed_files")
```




    ['param_2.yaml',
     'param_11.dill',
     'param_1.yaml',
     'param_10.txt',
     'param_21.ipynb']



### 9. Structure of commit tables

#### solution_description


```python
pd.DataFrame(pf2.commited_tables['b5c2e4a9bdcb57cc70bdb7310c7909cc1549550add79e3fbcc8aa1cf323cd8ca']['solution_description'])
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
      <th>deprecation_date</th>
      <th>maintainers</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>b5c2e4a9bdcb57cc70bdb7310c7909cc1549550add79e3fbcc8aa1cf323cd8ca</td>
      <td>new_example_solution</td>
      <td>Description of new example solution.</td>
      <td>2024-xx-xx</td>
      <td>None</td>
      <td>some text about maintainers credentials</td>
    </tr>
  </tbody>
</table>
</div>



#### solution_parameter_set


```python
param_set_id = 'a54f04d2ff154294309403206e059aec556cdcfa51120649ce663f3230a970d5'

pd.DataFrame(pf2.commited_tables['b5c2e4a9bdcb57cc70bdb7310c7909cc1549550add79e3fbcc8aa1cf323cd8ca']['solution_parameter_set'][param_set_id])
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
      <td>b5c2e4a9bdcb57cc70bdb7310c7909cc1549550add79e3fbcc8aa1cf323cd8ca</td>
      <td>a54f04d2ff154294309403206e059aec556cdcfa51120649ce663f3230a970d5</td>
      <td>PRODUCTION</td>
      <td>2024-05-07 19:51:13</td>
    </tr>
  </tbody>
</table>
</div>



#### parameter_set


```python
pd.DataFrame(pf2.commited_tables['b5c2e4a9bdcb57cc70bdb7310c7909cc1549550add79e3fbcc8aa1cf323cd8ca']\
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
      <td>a54f04d2ff154294309403206e059aec556cdcfa51120649ce663f3230a970d5</td>
      <td>4cea5b09e77da310c5105978f2ceea5c5d8c9c7b65d0e00b45135ea90fc011af</td>
    </tr>
    <tr>
      <th>1</th>
      <td>a54f04d2ff154294309403206e059aec556cdcfa51120649ce663f3230a970d5</td>
      <td>bf11768decb1d0204e2636edd05c354573d473e67f1b048369b2ee99c865bf5f</td>
    </tr>
    <tr>
      <th>2</th>
      <td>a54f04d2ff154294309403206e059aec556cdcfa51120649ce663f3230a970d5</td>
      <td>9a4a3ace265c9bf2facc0044ca24260c42805c6e7b2a608dfd2f56a54d9d36be</td>
    </tr>
    <tr>
      <th>3</th>
      <td>a54f04d2ff154294309403206e059aec556cdcfa51120649ce663f3230a970d5</td>
      <td>ace2f31433212fbf9e764069a30a7675ca78f496d31f061d06d0a0420fc52768</td>
    </tr>
    <tr>
      <th>4</th>
      <td>a54f04d2ff154294309403206e059aec556cdcfa51120649ce663f3230a970d5</td>
      <td>1a4f19ee9e186ee739daecbc778501c5851d3fb5d05c4a3c1200e599855e8689</td>
    </tr>
  </tbody>
</table>
</div>



#### parameter_set_description


```python
pd.DataFrame(pf2.commited_tables['b5c2e4a9bdcb57cc70bdb7310c7909cc1549550add79e3fbcc8aa1cf323cd8ca']\
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
      <td>a54f04d2ff154294309403206e059aec556cdcfa51120649ce663f3230a970d5</td>
      <td>test_set</td>
      <td>example parameters for test purposes</td>
    </tr>
  </tbody>
</table>
</div>



#### parameter_description


```python
pd.DataFrame([tab for param_id, tab_list in pf2.commited_tables['b5c2e4a9bdcb57cc70bdb7310c7909cc1549550add79e3fbcc8aa1cf323cd8ca']\
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
      <td>4cea5b09e77da310c5105978f2ceea5c5d8c9c7b65d0e00b45135ea90fc011af</td>
      <td>param_1</td>
      <td></td>
      <td>param_1.yaml</td>
      <td>yaml</td>
    </tr>
    <tr>
      <th>1</th>
      <td>bf11768decb1d0204e2636edd05c354573d473e67f1b048369b2ee99c865bf5f</td>
      <td>param_2</td>
      <td></td>
      <td>param_2.yaml</td>
      <td>yaml</td>
    </tr>
    <tr>
      <th>2</th>
      <td>9a4a3ace265c9bf2facc0044ca24260c42805c6e7b2a608dfd2f56a54d9d36be</td>
      <td>param_10</td>
      <td></td>
      <td>param_10.txt</td>
      <td>txt</td>
    </tr>
    <tr>
      <th>3</th>
      <td>ace2f31433212fbf9e764069a30a7675ca78f496d31f061d06d0a0420fc52768</td>
      <td>param_11</td>
      <td></td>
      <td>param_11.dill</td>
      <td>other</td>
    </tr>
    <tr>
      <th>4</th>
      <td>1a4f19ee9e186ee739daecbc778501c5851d3fb5d05c4a3c1200e599855e8689</td>
      <td>param_21</td>
      <td></td>
      <td>param_21.ipynb</td>
      <td>other</td>
    </tr>
  </tbody>
</table>
</div>



#### parameter_attribute


```python
pd.DataFrame([tab for param_id, tab_list in pf2.commited_tables['b5c2e4a9bdcb57cc70bdb7310c7909cc1549550add79e3fbcc8aa1cf323cd8ca']\
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
      <td>4cea5b09e77da310c5105978f2ceea5c5d8c9c7b65d0e00b45135ea90fc011af</td>
      <td>ee25af17445d7622cbf61a5b9424246a1f3104704b68bd31b9b7532471d492e5</td>
      <td>None</td>
    </tr>
    <tr>
      <th>1</th>
      <td>4cea5b09e77da310c5105978f2ceea5c5d8c9c7b65d0e00b45135ea90fc011af</td>
      <td>8b5b2be24e60ba407b90967820da8a1385a6d67691a02bc663703160ef655101</td>
      <td>None</td>
    </tr>
    <tr>
      <th>2</th>
      <td>4cea5b09e77da310c5105978f2ceea5c5d8c9c7b65d0e00b45135ea90fc011af</td>
      <td>52ea872c99c586530348ba8902dcab831761673d25cf1cb0023576820289ce6b</td>
      <td>None</td>
    </tr>
    <tr>
      <th>3</th>
      <td>bf11768decb1d0204e2636edd05c354573d473e67f1b048369b2ee99c865bf5f</td>
      <td>7d5ee0e0cd00c3703e5f346c6887baf503faaf9fe090774f6866311f4fa34179</td>
      <td>None</td>
    </tr>
    <tr>
      <th>4</th>
      <td>bf11768decb1d0204e2636edd05c354573d473e67f1b048369b2ee99c865bf5f</td>
      <td>ee25af17445d7622cbf61a5b9424246a1f3104704b68bd31b9b7532471d492e5</td>
      <td>7d5ee0e0cd00c3703e5f346c6887baf503faaf9fe090774f6866311f4fa34179</td>
    </tr>
    <tr>
      <th>5</th>
      <td>bf11768decb1d0204e2636edd05c354573d473e67f1b048369b2ee99c865bf5f</td>
      <td>3367512147bf19ae99c986b356af11dcdc067376aa1b79eb8ba8f61324e8dc18</td>
      <td>7d5ee0e0cd00c3703e5f346c6887baf503faaf9fe090774f6866311f4fa34179</td>
    </tr>
    <tr>
      <th>6</th>
      <td>bf11768decb1d0204e2636edd05c354573d473e67f1b048369b2ee99c865bf5f</td>
      <td>341769820d8937a5c9f9b980eefca37f3f37fcc6fd01c6f4c930fdb9d5dd5128</td>
      <td>7d5ee0e0cd00c3703e5f346c6887baf503faaf9fe090774f6866311f4fa34179</td>
    </tr>
    <tr>
      <th>7</th>
      <td>bf11768decb1d0204e2636edd05c354573d473e67f1b048369b2ee99c865bf5f</td>
      <td>2e8b00e571f9d835d3f022a9ff49b9779034ab21bffdcde075d9d729fabeb960</td>
      <td>341769820d8937a5c9f9b980eefca37f3f37fcc6fd01c6f4c930fdb9d5dd5128</td>
    </tr>
    <tr>
      <th>8</th>
      <td>bf11768decb1d0204e2636edd05c354573d473e67f1b048369b2ee99c865bf5f</td>
      <td>ecd93cf051988b23b3590415f4e7d550de264600d7d2af8704c973b9c98ca6a9</td>
      <td>341769820d8937a5c9f9b980eefca37f3f37fcc6fd01c6f4c930fdb9d5dd5128</td>
    </tr>
    <tr>
      <th>9</th>
      <td>9a4a3ace265c9bf2facc0044ca24260c42805c6e7b2a608dfd2f56a54d9d36be</td>
      <td>fa4e8d81f4dbe6d306aff59bea4693d325a203be5d5b9fde5d5f1e7cce26b861</td>
      <td>None</td>
    </tr>
    <tr>
      <th>10</th>
      <td>9a4a3ace265c9bf2facc0044ca24260c42805c6e7b2a608dfd2f56a54d9d36be</td>
      <td>c26e7e96f0f3647c159b0934f4dc55207ac059abb56005d7a8acd8344ef14798</td>
      <td>fa4e8d81f4dbe6d306aff59bea4693d325a203be5d5b9fde5d5f1e7cce26b861</td>
    </tr>
    <tr>
      <th>11</th>
      <td>9a4a3ace265c9bf2facc0044ca24260c42805c6e7b2a608dfd2f56a54d9d36be</td>
      <td>f7cd339f77c1799f399d8ebcbb27f2d41a448622254d64e9270ae2316211ac1d</td>
      <td>c26e7e96f0f3647c159b0934f4dc55207ac059abb56005d7a8acd8344ef14798</td>
    </tr>
    <tr>
      <th>12</th>
      <td>9a4a3ace265c9bf2facc0044ca24260c42805c6e7b2a608dfd2f56a54d9d36be</td>
      <td>15a33fe62774a1857b404f453ba1195eb4355e10bc9519f2f991dd7ba8db19b7</td>
      <td>f7cd339f77c1799f399d8ebcbb27f2d41a448622254d64e9270ae2316211ac1d</td>
    </tr>
    <tr>
      <th>13</th>
      <td>9a4a3ace265c9bf2facc0044ca24260c42805c6e7b2a608dfd2f56a54d9d36be</td>
      <td>99761e3d58bc213dc3ab33f2dc8dabe5f97d3aea6b59cd367d40b76937f49aa6</td>
      <td>15a33fe62774a1857b404f453ba1195eb4355e10bc9519f2f991dd7ba8db19b7</td>
    </tr>
    <tr>
      <th>14</th>
      <td>9a4a3ace265c9bf2facc0044ca24260c42805c6e7b2a608dfd2f56a54d9d36be</td>
      <td>036a9c122c1f4c9304afa23c4d1fce5224c270a206889afa689f3efb36ff368d</td>
      <td>99761e3d58bc213dc3ab33f2dc8dabe5f97d3aea6b59cd367d40b76937f49aa6</td>
    </tr>
    <tr>
      <th>15</th>
      <td>9a4a3ace265c9bf2facc0044ca24260c42805c6e7b2a608dfd2f56a54d9d36be</td>
      <td>e72aa8015688052f4e7fddbf4c74e5bf2bd74239ebf3902a5fdc008ecb03aa46</td>
      <td>036a9c122c1f4c9304afa23c4d1fce5224c270a206889afa689f3efb36ff368d</td>
    </tr>
    <tr>
      <th>16</th>
      <td>9a4a3ace265c9bf2facc0044ca24260c42805c6e7b2a608dfd2f56a54d9d36be</td>
      <td>0ae8eda3dbeedbc17e27a679c5426dd3af1434f7c37b4ecd3b2fb5c492272b75</td>
      <td>e72aa8015688052f4e7fddbf4c74e5bf2bd74239ebf3902a5fdc008ecb03aa46</td>
    </tr>
    <tr>
      <th>17</th>
      <td>9a4a3ace265c9bf2facc0044ca24260c42805c6e7b2a608dfd2f56a54d9d36be</td>
      <td>cedcfbb0d95798514b6aaf30118fff7b46f863f1bc8b80bb2ddd2145e5b3f318</td>
      <td>0ae8eda3dbeedbc17e27a679c5426dd3af1434f7c37b4ecd3b2fb5c492272b75</td>
    </tr>
    <tr>
      <th>18</th>
      <td>ace2f31433212fbf9e764069a30a7675ca78f496d31f061d06d0a0420fc52768</td>
      <td>ace2f31433212fbf9e764069a30a7675ca78f496d31f061d06d0a0420fc52768</td>
      <td>None</td>
    </tr>
    <tr>
      <th>19</th>
      <td>1a4f19ee9e186ee739daecbc778501c5851d3fb5d05c4a3c1200e599855e8689</td>
      <td>87d93e1862f0f58199c3fcb7114b92fe59f03581804b1c8419868fb00ff8a469</td>
      <td>None</td>
    </tr>
    <tr>
      <th>20</th>
      <td>1a4f19ee9e186ee739daecbc778501c5851d3fb5d05c4a3c1200e599855e8689</td>
      <td>b4a705d09aa0361f4db453da32abb05a5c4e0249d6180d2b8a58d72d08dbd6a0</td>
      <td>87d93e1862f0f58199c3fcb7114b92fe59f03581804b1c8419868fb00ff8a469</td>
    </tr>
    <tr>
      <th>21</th>
      <td>1a4f19ee9e186ee739daecbc778501c5851d3fb5d05c4a3c1200e599855e8689</td>
      <td>e4e2c33a2ea67f34bf3ac1e9d99edaad501c7dc4ea82f4b60e9d959418d8438d</td>
      <td>b4a705d09aa0361f4db453da32abb05a5c4e0249d6180d2b8a58d72d08dbd6a0</td>
    </tr>
    <tr>
      <th>22</th>
      <td>1a4f19ee9e186ee739daecbc778501c5851d3fb5d05c4a3c1200e599855e8689</td>
      <td>777abf12375b7f605b21535eb0d6232ce99581c6d2b1179af976cd0708ad27ff</td>
      <td>e4e2c33a2ea67f34bf3ac1e9d99edaad501c7dc4ea82f4b60e9d959418d8438d</td>
    </tr>
  </tbody>
</table>
</div>



#### attribute_values


```python
pd.DataFrame([tab for param_id, tab_list in pf2.commited_tables['b5c2e4a9bdcb57cc70bdb7310c7909cc1549550add79e3fbcc8aa1cf323cd8ca']\
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
      <th>previous_attribute_id</th>
      <th>attribute_name</th>
      <th>attribute_value</th>
      <th>attribute_value_type</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>ee25af17445d7622cbf61a5b9424246a1f3104704b68bd31b9b7532471d492e5</td>
      <td>None</td>
      <td>name</td>
      <td>Some name</td>
      <td>str</td>
    </tr>
    <tr>
      <th>1</th>
      <td>8b5b2be24e60ba407b90967820da8a1385a6d67691a02bc663703160ef655101</td>
      <td>None</td>
      <td>age</td>
      <td>111</td>
      <td>int</td>
    </tr>
    <tr>
      <th>2</th>
      <td>52ea872c99c586530348ba8902dcab831761673d25cf1cb0023576820289ce6b</td>
      <td>None</td>
      <td>country</td>
      <td>Some land</td>
      <td>str</td>
    </tr>
    <tr>
      <th>3</th>
      <td>ee25af17445d7622cbf61a5b9424246a1f3104704b68bd31b9b7532471d492e5</td>
      <td>None</td>
      <td>name</td>
      <td>Some name</td>
      <td>str</td>
    </tr>
    <tr>
      <th>4</th>
      <td>7d5ee0e0cd00c3703e5f346c6887baf503faaf9fe090774f6866311f4fa34179</td>
      <td>None</td>
      <td>employee</td>
      <td>{'name': 'Some name', 'id': 10293, 'contact': {'email': 'some.name...</td>
      <td>dict</td>
    </tr>
    <tr>
      <th>5</th>
      <td>3367512147bf19ae99c986b356af11dcdc067376aa1b79eb8ba8f61324e8dc18</td>
      <td>None</td>
      <td>id</td>
      <td>10293</td>
      <td>int</td>
    </tr>
    <tr>
      <th>6</th>
      <td>341769820d8937a5c9f9b980eefca37f3f37fcc6fd01c6f4c930fdb9d5dd5128</td>
      <td>None</td>
      <td>contact</td>
      <td>{'email': 'some.name@example.com', 'phone': '+1234567890'}</td>
      <td>dict</td>
    </tr>
    <tr>
      <th>7</th>
      <td>2e8b00e571f9d835d3f022a9ff49b9779034ab21bffdcde075d9d729fabeb960</td>
      <td>None</td>
      <td>email</td>
      <td>some.name@example.com</td>
      <td>str</td>
    </tr>
    <tr>
      <th>8</th>
      <td>ecd93cf051988b23b3590415f4e7d550de264600d7d2af8704c973b9c98ca6a9</td>
      <td>None</td>
      <td>phone</td>
      <td>+1234567890</td>
      <td>str</td>
    </tr>
    <tr>
      <th>9</th>
      <td>fa4e8d81f4dbe6d306aff59bea4693d325a203be5d5b9fde5d5f1e7cce26b861</td>
      <td>None</td>
      <td>0</td>
      <td>\X/Fc7;/v`6joU5z*n{35zFB&lt;&lt;6BMC,}/_04],&gt;v$Jr2&amp;0M_7qU'IY#6uO\$kEr.)Z...</td>
      <td>str</td>
    </tr>
    <tr>
      <th>10</th>
      <td>c26e7e96f0f3647c159b0934f4dc55207ac059abb56005d7a8acd8344ef14798</td>
      <td>None</td>
      <td>1</td>
      <td>A7J+1x5|?r]2zg54nxoa&gt;W*loh8Np~*9+*KxWLuD/Z5g!=DN&gt;}c#]Dt-&gt;tiov?|Ms....</td>
      <td>str</td>
    </tr>
    <tr>
      <th>11</th>
      <td>f7cd339f77c1799f399d8ebcbb27f2d41a448622254d64e9270ae2316211ac1d</td>
      <td>None</td>
      <td>2</td>
      <td>LUs%&lt;HRbNA_4:yYTh!!x&amp;oFZ201sQ7;~Q_IYr"lGRMd=xx,r}|n8zHIP6%JN)",vQI...</td>
      <td>str</td>
    </tr>
    <tr>
      <th>12</th>
      <td>15a33fe62774a1857b404f453ba1195eb4355e10bc9519f2f991dd7ba8db19b7</td>
      <td>None</td>
      <td>3</td>
      <td>b&amp;z(/Z{s@U&gt;@o!}{+(mmygo}u~AHgdu&gt;:jz4fNBm0;Q6'o+f%H/z3^8Hh!w&lt;#z.~21...</td>
      <td>str</td>
    </tr>
    <tr>
      <th>13</th>
      <td>99761e3d58bc213dc3ab33f2dc8dabe5f97d3aea6b59cd367d40b76937f49aa6</td>
      <td>None</td>
      <td>4</td>
      <td>.#;5Cu]5~8ZmYBLI4w)|h=)C&lt;(#`KSoM,`7n?dun7]LX&gt;j7/U&gt;Jf||4`AN_u*W!*3)...</td>
      <td>str</td>
    </tr>
    <tr>
      <th>14</th>
      <td>036a9c122c1f4c9304afa23c4d1fce5224c270a206889afa689f3efb36ff368d</td>
      <td>None</td>
      <td>5</td>
      <td>0S)*}6"i)kUg3=n:}&gt;Ji)!"BTbzsdgps8{cR]`.41QJ&lt;O{wr[}}gGan_O63D0WBr]&lt;...</td>
      <td>str</td>
    </tr>
    <tr>
      <th>15</th>
      <td>e72aa8015688052f4e7fddbf4c74e5bf2bd74239ebf3902a5fdc008ecb03aa46</td>
      <td>None</td>
      <td>6</td>
      <td>Xb;IgM/`T:VY*6XQ:nvB3)&gt;@32w8H-cD"g&gt;x`MlWp_TnuyCaz62e??md&lt;8tR$Q=X7&lt;...</td>
      <td>str</td>
    </tr>
    <tr>
      <th>16</th>
      <td>0ae8eda3dbeedbc17e27a679c5426dd3af1434f7c37b4ecd3b2fb5c492272b75</td>
      <td>None</td>
      <td>7</td>
      <td>pq.%\nmm;M!^cyS|ApMpnjUS&lt;#Ov?e+n"wX/to.wjifCG.fKK@6gI+Wvax&amp;}j18R8p...</td>
      <td>str</td>
    </tr>
    <tr>
      <th>17</th>
      <td>cedcfbb0d95798514b6aaf30118fff7b46f863f1bc8b80bb2ddd2145e5b3f318</td>
      <td>None</td>
      <td>8</td>
      <td>+-;Zt=ex</td>
      <td>str</td>
    </tr>
    <tr>
      <th>18</th>
      <td>ace2f31433212fbf9e764069a30a7675ca78f496d31f061d06d0a0420fc52768</td>
      <td>None</td>
      <td>0</td>
      <td>b'\x80\x04\x95h\x00\x00\x00\x00\x00\x00\x00}\x94(\x8c\x07integer\x...</td>
      <td>bytes</td>
    </tr>
    <tr>
      <th>19</th>
      <td>87d93e1862f0f58199c3fcb7114b92fe59f03581804b1c8419868fb00ff8a469</td>
      <td>None</td>
      <td>0</td>
      <td>b'{\n "cells": [\n  {\n   "cell_type": "markdown",\n   "metadata":...</td>
      <td>bytes</td>
    </tr>
    <tr>
      <th>20</th>
      <td>b4a705d09aa0361f4db453da32abb05a5c4e0249d6180d2b8a58d72d08dbd6a0</td>
      <td>None</td>
      <td>1</td>
      <td>xt/plain": [\n       "4"\n      ]\n     },\n     "execution_count"...</td>
      <td>bytes</td>
    </tr>
    <tr>
      <th>21</th>
      <td>e4e2c33a2ea67f34bf3ac1e9d99edaad501c7dc4ea82f4b60e9d959418d8438d</td>
      <td>None</td>
      <td>2</td>
      <td>"language": "python",\n   "name": "python3"\n  },\n  "language_...</td>
      <td>bytes</td>
    </tr>
    <tr>
      <th>22</th>
      <td>777abf12375b7f605b21535eb0d6232ce99581c6d2b1179af976cd0708ad27ff</td>
      <td>None</td>
      <td>3</td>
      <td>r": "python",\n   "pygments_lexer": "ipython3",\n   "version": "3....</td>
      <td>bytes</td>
    </tr>
  </tbody>
</table>
</div>



### 10. Scores

##### I. Attribute overlap ratio

AOR represents an overlap ratio between attribute ids that:

- belong to a parameter within parameter set
- belong to a parameter sets within solution
- belong to a solution within solutions

The score is between $0$ and $1$, and the greater the score, the greater is an overlap between attribute ids within select group and non unique attribute ids.

##### II. Parameter overlap ratio

POR represents an overlap ratio between parameter ids that:

- belong to a parameter sets within solution
- belong to a solution within solutions

The score is between $0$ and $1$, and the greater the score, the greater is an overlap between parameter ids within select group and non unique parameter ids.
