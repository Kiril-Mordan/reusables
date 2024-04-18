# Grid Looper

A tool to run experiments based on defined grid and function with single iteration.


```python
import sys
sys.path.append('../')
from python_modules.gridlooper import GridLooper
```

## Usage examples

The examples contain:

1. preparing runner function
2. preparing search grid
3. running experiments
4. analysing results
    

### 1. Preparing runner function

Runner funtion should contain logic of experiment in a way that the parameters could be supplied with `embedder_params` 


```python
def runner_function(runner_params : dict, c : int):

    result = int(runner_params['a']) + runner_params['b'] + c

    return result
```

### 2. Preparing search grid

Experiment combos can be defined in short form, transformed into a list and filtered with `exlusion_combos`. Some of the parameters in experiment definition could be ignored durring experiment with a use of `exclusion_keys` parameter.


```python
experiments_settings = {
    'runner_params': {'a' : ['1', '2','4'],
                        'b' : [2, 6,10,100]},

    'c' : [100, 500],#, 1000, 5000]
    'name' : 'example experiment'
}

exclusion_keys = {'name'}

exclusion_combos = [{'runner_params': {'a': ['1','2'],
                                       'b': [100, 6,10]}}]
```


```python
gl = GridLooper(
    # dictionary of all possible parameter combos
    experiments_settings = experiments_settings,
    # keys from the experiments_settings to be ignored
    exclusion_keys = exclusion_keys,
    # combos from experiments_settings to be exluded
    exclusion_combos = exclusion_combos,
    # function that be run for each of experiment combos
    runner_function = runner_function,
    # optional parameter to be supplied to runner function outside of experiment settings
    data = None,
    # path to save experiment results
    save_path = 'example_run.dill')
```


```python
gl.prepare_search_grid(
    # optional if definer earlier
    experiments_settings = experiments_settings,
    exclusion_keys = exclusion_keys,
    exclusion_combos = exclusion_combos
)


gl.experiment_configs
```




    [{'runner_params': {'a': '1', 'b': 2},
      'c': 100,
      'config_id': '54eac3ee5ce6ae6d126502ee87dbbafce54111b346b895e1d5e29c50097fa800'},
     {'runner_params': {'a': '1', 'b': 2},
      'c': 500,
      'config_id': 'b2ef1c49a36375e88203f9ff1f01db69457fc9eb6435333aaafee68bb871d9da'},
     {'runner_params': {'a': '2', 'b': 2},
      'c': 100,
      'config_id': '4b1a723841dbf9f6e2a415159d0deb938373ba21506285289e46cafdcf455f05'},
     {'runner_params': {'a': '2', 'b': 2},
      'c': 500,
      'config_id': '44a22efdfe7e385b4fbaeb84976ac0d10703a98902ce134cddd1000e09ba156a'},
     {'runner_params': {'a': '4', 'b': 2},
      'c': 100,
      'config_id': '6dc5a94f832532513b1d739fdad694029b6b9d97cec9fa869ce3d75b822c23ce'},
     {'runner_params': {'a': '4', 'b': 2},
      'c': 500,
      'config_id': '9e7ec3d2e9d7d5ccf4b8c05b9a7a145fc443f77cd7031dcdaf139a77f88d5944'},
     {'runner_params': {'a': '4', 'b': 6},
      'c': 100,
      'config_id': 'dcd7c1aeb1b3c41ab924ece9ed471d682cef319304a9675dfd1f7d27f6e29c7c'},
     {'runner_params': {'a': '4', 'b': 6},
      'c': 500,
      'config_id': 'ad38629f25dd962d157ee8b36b1fc34a54079f8b08d0d4e79fd45cecfa167d49'},
     {'runner_params': {'a': '4', 'b': 10},
      'c': 100,
      'config_id': '6cd8cc53587798f4fc2583a122a7cad6e79cb7b6c10639e6a9714d12fa2c3092'},
     {'runner_params': {'a': '4', 'b': 10},
      'c': 500,
      'config_id': '495efcc2399e24fed5a5dee4b3909f27688b7723eb62b28be6ff6eb74c4e8574'},
     {'runner_params': {'a': '4', 'b': 100},
      'c': 100,
      'config_id': '2dcdd7a719ce8fa4731c8d9adefd131d809fd29e014aa9acd3be8a6538cc8765'},
     {'runner_params': {'a': '4', 'b': 100},
      'c': 500,
      'config_id': '64f83d857c2c3a0030bd187330da30dc6d4aaf2ae1418f150b9902a269a4f3d8'}]



### 3. Running experiments

`executing_experimets` function will run `runner_function` for each set of parameters from defined `experiment_configs` for a select loop strategy.


```python
gl.executing_experimets(
    # optional of defined earlier
    runner_function = runner_function,
    experiment_configs = gl.experiment_configs,
    data = None,
    loop_type= 'brute',
    save_path = 'example_run.dill'
)
```

    Looping:   0%|          | 0/12 [00:00<?, ?item/s]

    Looping: 100%|██████████| 12/12 [00:00<00:00, 97731.36item/s]

    


### 4. Analysing results


```python
gl.experiment_results['results']
```




    {'54eac3ee5ce6ae6d126502ee87dbbafce54111b346b895e1d5e29c50097fa800': 103,
     'b2ef1c49a36375e88203f9ff1f01db69457fc9eb6435333aaafee68bb871d9da': 503,
     '4b1a723841dbf9f6e2a415159d0deb938373ba21506285289e46cafdcf455f05': 104,
     '44a22efdfe7e385b4fbaeb84976ac0d10703a98902ce134cddd1000e09ba156a': 504,
     '6dc5a94f832532513b1d739fdad694029b6b9d97cec9fa869ce3d75b822c23ce': 106,
     '9e7ec3d2e9d7d5ccf4b8c05b9a7a145fc443f77cd7031dcdaf139a77f88d5944': 506,
     'dcd7c1aeb1b3c41ab924ece9ed471d682cef319304a9675dfd1f7d27f6e29c7c': 110,
     'ad38629f25dd962d157ee8b36b1fc34a54079f8b08d0d4e79fd45cecfa167d49': 510,
     '6cd8cc53587798f4fc2583a122a7cad6e79cb7b6c10639e6a9714d12fa2c3092': 114,
     '495efcc2399e24fed5a5dee4b3909f27688b7723eb62b28be6ff6eb74c4e8574': 514,
     '2dcdd7a719ce8fa4731c8d9adefd131d809fd29e014aa9acd3be8a6538cc8765': 204,
     '64f83d857c2c3a0030bd187330da30dc6d4aaf2ae1418f150b9902a269a4f3d8': 604}


