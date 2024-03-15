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




    [{'c': 100,
      'runner_params': {'a': '1', 'b': 2},
      'config_id': '8562104a0147be32e0a7611eb5229773906d12c2614826c5fc16b05b76466aba'},
     {'c': 100,
      'runner_params': {'a': '2', 'b': 2},
      'config_id': 'a6148a8d9c48e610c40e5fdde002c1601a0c0344b7df4dcd458dbe7e6fe27772'},
     {'c': 100,
      'runner_params': {'a': '4', 'b': 2},
      'config_id': '53bc174470bf27ac5b821773d691f6290dd546a703461cde818e1b18eb5224c8'},
     {'c': 100,
      'runner_params': {'a': '4', 'b': 6},
      'config_id': 'c341935f88d73f9c0919bdfb061a6d6548ceb83a24e88ce2bda409e489e57e11'},
     {'c': 100,
      'runner_params': {'a': '4', 'b': 10},
      'config_id': 'd5643e3314c572d7c65c86cf5f36686891b306473f5958f7d019ecaad768a6d8'},
     {'c': 100,
      'runner_params': {'a': '4', 'b': 100},
      'config_id': '4500841c83a8731c56f661b570a7f2a754e2808c41de44a5dd7097accdb437ce'},
     {'c': 500,
      'runner_params': {'a': '1', 'b': 2},
      'config_id': '3757452851f2829021b4cf33d08f0fe8049ca4617e6dead2f78aa45db48eeeb4'},
     {'c': 500,
      'runner_params': {'a': '2', 'b': 2},
      'config_id': '598e1072c1d2953abffc9cb2518b09daec7fc78d261920a328a9396820cd3edd'},
     {'c': 500,
      'runner_params': {'a': '4', 'b': 2},
      'config_id': '052e617f5141d37da96e804759603c6d0e8df10dfb5489cf383ed2813b8f87b8'},
     {'c': 500,
      'runner_params': {'a': '4', 'b': 6},
      'config_id': '5c862e5bfeab31aa17483a39a92b455401e49679b1fa3f191beaebec74b396d7'},
     {'c': 500,
      'runner_params': {'a': '4', 'b': 10},
      'config_id': 'aded884015788f0e9152cbb286604945e7a2f109309a8059efbe35a801ff8b54'},
     {'c': 500,
      'runner_params': {'a': '4', 'b': 100},
      'config_id': 'c2900743d454591bcce89c767591edf9044c2c77baae1e271f19a3570f2b0c8f'}]



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

    Looping: 100%|██████████| 12/12 [00:00<00:00, 117872.71item/s]

    


### 4. Analysing results


```python
gl.experiment_results['results']
```




    {'8562104a0147be32e0a7611eb5229773906d12c2614826c5fc16b05b76466aba': 103,
     'a6148a8d9c48e610c40e5fdde002c1601a0c0344b7df4dcd458dbe7e6fe27772': 104,
     '53bc174470bf27ac5b821773d691f6290dd546a703461cde818e1b18eb5224c8': 106,
     'c341935f88d73f9c0919bdfb061a6d6548ceb83a24e88ce2bda409e489e57e11': 110,
     'd5643e3314c572d7c65c86cf5f36686891b306473f5958f7d019ecaad768a6d8': 114,
     '4500841c83a8731c56f661b570a7f2a754e2808c41de44a5dd7097accdb437ce': 204,
     '3757452851f2829021b4cf33d08f0fe8049ca4617e6dead2f78aa45db48eeeb4': 503,
     '598e1072c1d2953abffc9cb2518b09daec7fc78d261920a328a9396820cd3edd': 504,
     '052e617f5141d37da96e804759603c6d0e8df10dfb5489cf383ed2813b8f87b8': 506,
     '5c862e5bfeab31aa17483a39a92b455401e49679b1fa3f191beaebec74b396d7': 510,
     'aded884015788f0e9152cbb286604945e7a2f109309a8059efbe35a801ff8b54': 514,
     'c2900743d454591bcce89c767591edf9044c2c77baae1e271f19a3570f2b0c8f': 604}


