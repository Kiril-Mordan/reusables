"""
Grid Looper

A tool to run experiments based on defined grid and function with single iteration.
"""

import logging
import attr #>=22.2.0
from itertools import product
import dill #==0.3.7
## for making keys
import hashlib
import json
## to track time
from datetime import datetime
from tqdm import tqdm


__design_choices__ = {
}

# Metadata for package creation
__package_metadata__ = {
    "author": "Kyrylo Mordan",
    "author_email": "parachute.repo@gmail.com",
    "description": "A tool to run experiments based on defined grid and function with single iteration.",
    # Add other metadata as needed
}

@attr.s
class GridLooper:

    # for defining grid
    experiments_settings = attr.ib(default=None)
    exclusion_keys = attr.ib(default=None)
    exclusion_combos = attr.ib(default=None)

    # for runnning experiment
    runner_function = attr.ib(default=None)
    loop_type = attr.ib(default='brute')
    data = attr.ib(default=None)

    # for saving
    save_path = attr.ib(default='./experiments.dill')

    # outputs
    experiment_configs = attr.ib(default=None,init=None)
    experiment_results = attr.ib(default=None,init=None)
    experiment_config_ids = attr.ib(default=None,init=None)

    logger = attr.ib(default=None)
    logger_name = attr.ib(default='Similarity search')
    loggerLvl = attr.ib(default=logging.INFO)
    logger_format = attr.ib(default=None)


    def __attrs_post_init__(self):
        self._initialize_logger()


    def _initialize_logger(self):

        """
        Initialize a logger for the class instance based on the specified logging level and logger name.
        """

        if self.logger is None:
            logging.basicConfig(level=self.loggerLvl, format=self.logger_format)
            logger = logging.getLogger(self.logger_name)
            logger.setLevel(self.loggerLvl)

            self.logger = logger

#### DEFINING SEARCH GRID

    def hash_string_sha256(self,input_string):
        return hashlib.sha256(input_string.encode()).hexdigest()

    def _make_key(self,d):

        input_string = json.dumps(d)

        return self.hash_string_sha256(input_string)

    def _expand_dict_combinations(self, settings_dict : dict) -> list:
        """
        Generate all combinations for keys in a dictionary, handling both
        dictionary and non-dictionary values.
        """
        combinations = []
        for key, values in settings_dict.items():
            if isinstance(values, dict):
                # Generate combinations for nested dictionaries
                nested_combinations = list(product(*[[(nested_key, value) for value in nested_values] for nested_key, nested_values in values.items()]))
                combinations.extend([(key, dict(combo)) for combo in nested_combinations])
            else:
                # Directly use values for non-dictionary types
                combinations.extend([(key, value) for value in values])
        return combinations

    def _generate_experiment_configurations(self,
                                           experiments_settings : dict,
                                           excepted_keys : dict):
        """
        Generate all possible configurations from experiment settings, excluding specified keys.
        """
        # Extract keys for combination generation, excluding excepted keys
        if excepted_keys is not None:
            keys_to_combine = set(experiments_settings.keys()) - excepted_keys
        else:
            keys_to_combine = set(experiments_settings.keys())

        # Generate combinations for each key
        all_combinations = [self._expand_dict_combinations({key: experiments_settings[key]}) for key in keys_to_combine if key in experiments_settings]

        # Compute the cartesian product of all combinations
        product_combinations = list(product(*all_combinations))

        # Convert combinations into dictionary format
        experiment_configs = []
        for combination in product_combinations:
            config = {}
            for key, value in combination:
                if key in config and isinstance(config[key], dict) and isinstance(value, dict):
                    # Merge dictionaries if key already exists
                    config[key].update(value)
                else:
                    config[key] = value
            config['config_id'] = self._make_key(config)
            experiment_configs.append(config)

        return experiment_configs

    def _is_subset(self,
                   dict1 : dict,
                   dict2 : dict) -> bool:
        """
        Recursively check if dict2 is a subset of dict1.
        """
        for key, value in dict2.items():
            if key not in dict1:
                return False
            if isinstance(value, dict):
                if not isinstance(dict1[key], dict) or not self._is_subset(dict1[key], value):
                    return False
            elif dict1[key] != value and key != 'config_id':
                return False
        return True

    def _filter_dicts(self,
                      main_list : list,
                      filter_list : list) -> list:
        """
        Filter out items from main_list that match any of the conditions specified in filter_list.
        This function supports nested dictionaries of any depth.
        """
        filtered_list = [
            item for item in main_list
            if not any(self._is_subset(item, filter_condition) for filter_condition in filter_list)
        ]
        return filtered_list

    def _make_exclusion_configs(self, exlusion_combos) -> list :
        """
        For each dict in provides exclusion combons, expand it into a list of configs
        and combine lists from each element into one list.
        """

        exclusion_configs = []

        for exlusion_combo in exlusion_combos:

            exclusion_config = self._generate_experiment_configurations(exlusion_combo, excepted_keys=None)
            exclusion_configs = exclusion_configs + exclusion_config

        return exclusion_configs


    def prepare_search_grid(self,
                            experiments_settings : dict = None,
                            exclusion_keys : dict = None,
                            exclusion_combos : list = None):

        """
        Expands settings into search grid in a form of a list of indiviadual sets
        of parameters that could be fed into provides function later. It also
        exludes undesirable combonations from the grid and keys that don't become
        a part of provided function params.
        """

        if experiments_settings is None:
            experiments_settings = self.experiments_settings

        if exclusion_combos is None:
            exclusion_combos = self.exclusion_combos

        if exclusion_keys is None:
            exclusion_keys = self.exclusion_keys

        # Generate the configurations
        experiment_configs = self._generate_experiment_configurations(experiments_settings = experiments_settings ,
                                                                      excepted_keys = exclusion_keys)

        # Make exlusion configs if provides
        if exclusion_combos is not None:
            exclusion_configs = self._make_exclusion_configs(exclusion_combos)
            # filter experiment_configs with exlusion_combos
            experiment_configs = self._filter_dicts(experiment_configs, exclusion_configs)

        self.experiment_configs = experiment_configs

#### LOOP STRATEGIES

    def _brute_loop(self, func, grid_list : list, data : dict):

        loop_res = {}
        loop_time = {}
        experiment_config_ids = {}

        for grid_elem in tqdm(grid_list, desc="Looping", unit="item"):
            config_id = grid_elem['config_id']
            del grid_elem['config_id']
            experiment_config_ids[config_id] = grid_elem
            exec_start = datetime.now()
            if data:
                loop_res[config_id] = func(**grid_elem, data = data)
            else:
                loop_res[config_id] = func(**grid_elem)
            loop_time[config_id] = datetime.now() - exec_start

        return loop_res, loop_time, experiment_config_ids

    def _loop(self, loop_type : str, func, grid_list : list, data : dict):

        if loop_type == 'brute':
            loop_res, loop_time, experiment_config_ids = self._brute_loop(func, grid_list, data)

        return loop_res, loop_time, experiment_config_ids


#### EXECUTION LOOPS

    def executing_experimets(self,
                             runner_function = None,
                             experiment_configs : list = None,
                             data : dict = None,
                             loop_type : str = None,
                             save_path : str = None):


        """
        Running experiments with runner funtion for predefines configs and save results.
        """

        if runner_function is None:
            runner_function = self.runner_function

        if experiment_configs is None:
            experiment_configs = self.experiment_configs

        if loop_type is None:
            loop_type = self.loop_type

        if save_path is None:
            save_path = self.save_path

        if data is None:
            data = self.data


        self.runner_results, self.runner_time, self.experiment_config_ids = self._loop(loop_type = loop_type,
                   func = runner_function,
                   grid_list = experiment_configs,
                   data = data)

        self.experiment_results = {'settings' : self.experiments_settings,
                                   'experiment_config_ids' : self.experiment_config_ids,
                              'exlusions' : self.exclusion_combos,
                              'results' : self.runner_results,
                              'time' : self.runner_time}


        with open(save_path, 'wb') as file:
            dill.dump(self.experiment_results, file)


