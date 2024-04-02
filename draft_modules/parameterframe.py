"""
Parameter frame

The module provides an interface for managing solution parameters.
It allows for the structured storage and retrieval of parameter sets from a database.
"""

import attr
import os
import random
import dill
import hashlib
from datetime import datetime
from mocker_db import MockerDB
import yaml
from collections import defaultdict
import logging
import ast

__design_choices__ = {
    "FileTypeHandler" : ['prepares one parameter file and reconstructs one parameter file at a time',
                         'txt and yaml files can be processed',
                         'yaml files are not reconstructed 1to1 but are first make into python dictionary, with python type mapping'],
    "ParameterFrame" : ['parameter_names and paramer_description are optional']
}


@attr.s
class FileTypeHandler:

    """
    Handles raw files, processes them for storage
    and reconstructs when pulling from storage.
    """

    # inputs
    file_path = attr.ib(default=None, type = str)

    # inputs for reconstruction
    parameter_name = attr.ib(default='', type = str)
    parameter_description = attr.ib(default='', type = str)
    parameter_attributes_list = attr.ib(default=None, type = list)
    attribute_values_list = attr.ib(default=None, type = list)

    parameter_id = attr.ib(default=None, type = str)

    file_type = attr.ib(default=None, type = str)
    file_content = attr.ib(default=None, type = str)


    # logger config
    logger = attr.ib(default=None)
    logger_name = attr.ib(default='FileTypeHandler')
    loggerLvl = attr.ib(default=logging.INFO)
    logger_format = attr.ib(default=None)


    def __attrs_post_init__(self):
        self._initialize_logger()


    def _initialize_logger(self):

        """
        Initialize a logger for the class instance based on the specified logging level and logger name.
        """

        if self.logger is None:
            logging.basicConfig(level=self.loggerLvl,
                                format=self.logger_format)
            logger = logging.getLogger(self.logger_name)
            logger.setLevel(self.loggerLvl)

            self.logger = logger

    def _type_map(self):

        """
        Returns type mapping to reconstruct yaml files.
        """

        # Map type name strings back to actual Python types
        TYPE_MAP = {
            'str': str,
            'int': int,
            'float': float,
            'list': list,
            'bool': bool,
            # Add more mappings as necessary for the types you expect
        }

        return TYPE_MAP


    def _generate_unique_id(self, txt : str) -> str:

        """
        Helper function to generate a unique ID for attribute entries
        """

        hash_id = hashlib.sha256(str(txt).encode()).hexdigest()
        return hash_id

    def _determine_file_type(self, file_path: str) -> str:

        """
        Determines filetype from extension.
        """

        # Check the file extension
        _, file_extension = os.path.splitext(file_path)

        if file_extension in ['.yml', '.yaml']:
            return 'yaml'
        if file_extension == '.txt':
            return 'txt'

        return 'unknown'

    def _load_file_content(self,
                            file_path: str,
                            file_type : str) -> str:

        """
        Load content based on type.
        """

        # Try to guess and load the file based on the extension
        try:
            if file_type in ['yml', 'yaml']:
                with open(file_path, 'r') as file:
                    content = yaml.safe_load(file)
                return content
            elif file_type == 'txt':
                with open(file_path, 'r') as file:
                    content = file.read()
                return content
            # elif file_extension == '.dill':
            #     with open(file_path, 'rb') as file:
            #         content = dill.load(file)
            #     return 'dill', content
            else:
                # Fallback or additional file types can be handled here
                return None
        except Exception as e:
            return 'error', str(e)

    def _make_parameter_description(self,
                     parameter_id : str,
                     parameter_name : str,
                     parameter_description : str,
                     file_name : str,
                     file_type : str):

        """
        Function to create paramter description.
        """

        parameter_description = [
            {
                'parameter_id' : parameter_id,
                'parameter_name' : parameter_name,
                'parameter_description' : parameter_description,
                'file_name': file_name,
                'file_type': file_type
            }
        ]

        return parameter_description

    def _prefilter_search_lists(self,
                                parameter_id : str,
                                parameter_attributes_list : list,
                                attribute_values_list : list) -> tuple:

        """
        From param lists, selects information related only to selected parameter_id.
        """

        parameter_attributes_list = [pa for pa in parameter_attributes_list \
            if pa['parameter_id'] == parameter_id]
        attribute_ids = [pa['attribute_id'] for pa in parameter_attributes_list]

        attribute_values_list = [at for at in attribute_values_list \
            if at['attribute_id'] in attribute_ids]

        return parameter_attributes_list, attribute_values_list

    def _process_txt(self,
                     content : dict,
                     parameter_id : str = None) -> tuple:

        """
        Function to process txt files.
        """

        parameter_attributes =[{
                'parameter_id' : parameter_id,
                'attribute_id': parameter_id,
                'previous_attribute_id': None
            }]

        # It's a value, add to attribute_values
        attribute_values = [{
            'attribute_id': parameter_id,
            'attribute_name': None,
            'attribute_value': str(content),
            'attribute_value_type': type(content).__name__
        }]

        return parameter_attributes, attribute_values


    def _process_yaml(self,
                     content : dict,
                     parent_id : str = None,
                     parameter_id : str = None) -> tuple:

        """
        Recursive function to process the YAML dictionary and turn it into list inputs.
        """

        parameter_attributes = []
        attribute_values = []

        for key, value in content.items():
            # Generate a unique ID for the attribute
            attribute_id = self._generate_unique_id(str(key)+str(value))

            parameter_attributes.append({
                'parameter_id' : parameter_id,
                'attribute_id': attribute_id,
                'previous_attribute_id': parent_id
            })

            # It's a value, add to attribute_values
            attribute_values.append({
                'attribute_id': attribute_id,
                'attribute_name': key,
                'attribute_value': str(value),
                'attribute_value_type': type(value).__name__
            })

            if isinstance(value, dict):

                # It's a nested dictionary, recurse
                sub_attrs, sub_vals = self._process_yaml(value, attribute_id, parameter_id)
                parameter_attributes.extend(sub_attrs)
                attribute_values.extend(sub_vals)
            elif isinstance(value, list):

                for item in value:

                    attribute_id = self._generate_unique_id(str(item))

                    parameter_attributes.append({
                        'parameter_id' : parameter_id,
                        'attribute_id': attribute_id,
                        'previous_attribute_id': attribute_id
                    })

                    attribute_values.append({
                        'attribute_id': attribute_id,
                        'attribute_name': key,
                        'attribute_value': item,
                        'attribute_value_type': type(item).__name__
                    })

        return parameter_attributes, attribute_values

    def _convert_value(self, value, value_type):
        # Handle simple types directly
        if value_type in ['int', 'float', 'bool']:
            return self._type_map()[value_type](value)
        elif value_type == 'list' or value_type == 'dict':
            try:
                # Use ast.literal_eval for safe evaluation of the string representation
                return ast.literal_eval(value)
            except (ValueError, SyntaxError):
                # Fallback to original value if conversion is not possible
                return value
        else:
            # Default fallback for types not explicitly handled
            return value

    def _reconstruct_yaml(self,
                          parameter_attributes_list : list,
                          attribute_values_list : list):

        """
        Reconstructing yaml files from param and attribute lists.
        """

        try:

            # Build a dictionary mapping from attribute_id to attribute_name
            id_to_name = {attr['attribute_id']: attr.get('attribute_name', None) for attr in attribute_values_list}

            # Build a nested dictionary to represent the hierarchy of the attributes
            nested_attrs = defaultdict(dict)


            # Create a mapping from attribute_id to attribute_name
            for attr in attribute_values_list:
                nested_attrs[attr['attribute_id']]['name'] = attr['attribute_name']
                nested_attrs[attr['attribute_id']]['value'] = attr['attribute_value']
                nested_attrs[attr['attribute_id']]['type'] = attr['attribute_value_type']

            # Add children based on previous_attribute_id
            for attr in parameter_attributes_list:
                if attr['previous_attribute_id']:
                    nested_attrs[attr['previous_attribute_id']].setdefault('children', []).append(attr['attribute_id'])

            # Recursive function to construct the nested dictionary
            def construct_dict(attr_id):
                if 'children' in nested_attrs[attr_id]:
                    # reconstruct differently for list
                    if nested_attrs[attr_id]['type'] == 'list':
                        return [construct_dict(child_id) for child_id in nested_attrs[attr_id]['children']]

                    return {id_to_name[child_id]: construct_dict(child_id) for child_id in nested_attrs[attr_id]['children']}
                else:

                    value = nested_attrs[attr_id]['value']
                    value_type = nested_attrs[attr_id]['type']
                    return  self._convert_value(value, value_type)

            # Start constructing the nested dictionary from the top-level attributes
            result = {}
            for attr in parameter_attributes_list:
                if attr['previous_attribute_id'] is None:
                    # We are at a root attribute
                    attr_name = id_to_name[attr['attribute_id']]
                    result[attr_name] = construct_dict(attr['attribute_id'])

        except Exception as e:
            raise Exception("Failure to reconstruct yaml file!", e)

        return result


    def _reconstruct_txt(self,
                         attribute_values_list : list):

        """
        Reconstructing txt files from param and attribute lists.
        """

        return attribute_values_list[0]['attribute_value']



    def process_file(self,
                     file_path : str = None,
                     parameter_name : str = None,
                     parameter_description : str = None) -> None:

        """
        Processes raw parameter file and prepares list of inputs for table handlers.
        """

        if file_path is None:
            file_path = self.file_path

        if parameter_name is None:
            parameter_name = self.parameter_name

        if parameter_description is None:
            parameter_description = self.parameter_description

        self.file_type = self._determine_file_type(file_path=file_path)
        self.file_content = self._load_file_content(file_path=file_path,
                                                               file_type=self.file_type)

        self.parameter_id = self._generate_unique_id(str(self.file_content))

        self.parameter_description = self._make_parameter_description(
            parameter_id = self.parameter_id,
            parameter_name = parameter_name,
            parameter_description = parameter_description,
            file_name = os.path.basename(file_path),
            file_type = self.file_type)

        if self.file_type == 'yaml':
            (self.parameter_attributes_list,
             self.attribute_values_list) = self._process_yaml(content=self.file_content,
                                                              parameter_id=self.parameter_id)

        if self.file_type == 'txt':
            (self.parameter_attributes_list,
             self.attribute_values_list) = self._process_txt(content=self.file_content,
                                                              parameter_id=self.parameter_id)




    def reconstruct_file(self,
                         file_path : str = None,
                         parameter_id : str = None,
                         parameter_attributes_list : list = None,
                         attribute_values_list : list = None) -> None:

        """
        Reconstructs raw file from pulled list from table handlers.
        """

        if file_path is None:
            file_path = self.file_path

        if parameter_id is None:
            parameter_id = self.parameter_id

        if parameter_id is None:
            raise ValueError("Provide parameter_id!")

        if parameter_attributes_list is None:
            parameter_attributes_list = self.parameter_attributes_list

        if parameter_attributes_list is None:
            raise ValueError("Provide parameter_attributes_list!")

        if attribute_values_list is None:
            attribute_values_list = self.attribute_values_list

        if attribute_values_list is None:
            raise ValueError("Provide attribute_values_list!")

        self.file_type = self._determine_file_type(file_path=file_path)

        if self.file_type not in ['yaml', 'txt']:
            raise ValueError(f"File type is {self.file_type}!")

        # selecting subset for specific parameter_id
        (parameter_attributes_list,
         attribute_values_list) = self._prefilter_search_lists(
             parameter_id = parameter_id,
             parameter_attributes_list = parameter_attributes_list,
             attribute_values_list = attribute_values_list
         )

        if self.file_type == 'yaml':
            self.file_content = self._reconstruct_yaml(attribute_values_list=attribute_values_list,
                                                        parameter_attributes_list=parameter_attributes_list)

            # Write the dictionary to a YAML file
            with open(file_path, 'w', encoding='utf-8') as file:
                yaml.dump(self.file_content, file, sort_keys=False)

        if self.file_type == 'txt':
            self.file_content = self._reconstruct_txt(attribute_values_list=attribute_values_list)

            # Write the dictionary to a YAML file
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(self.file_content)

@attr.s
class ComplexNameGenerator:

    seed = attr.ib(default=None)

    def generate_random_name(self, seed : int = None):

        """
        Generates random name that is combionation of color, adjective, noun and 3 digits
        """
        # Sample lists
        colors = ["red", "blue", "green", "yellow", "pink", "silver", "purple", "golden"]
        adjectives = ["fuzzy", "bright", "dark", "shiny", "giant", "tiny", "happy", "sad"]
        nouns = ["toaster", "refrigerator", "microwave", "laptop", "thermostat", "television", "car", "scooter"]

        if isinstance(seed, int):
            # Set the seed value
            random.seed(seed)

        # Randomly choose a word from each list
        color = random.choice(colors)
        adj = random.choice(adjectives)
        noun = random.choice(nouns)
        digits = random.randint(100, 999)
        # Combine them to form a name
        name = f"{color}_{adj}_{noun}_{digits}"

        return name




@attr.s
class ParameterFrame:

    params_path = attr.ib()

    # optional
    solution_id = attr.ib(default=None, type=str)
    param_names = attr.ib(default=None, type=dict)
    param_descriptions = attr.ib(default=None, type=dict)
    seed = attr.ib(default=None, type=int)

    # dependancies
    file_type_handler = attr.ib(default=FileTypeHandler)
    name_generator = attr.ib(default=ComplexNameGenerator)

    # inner
    solutions = attr.ib(default={})
    param_sets = attr.ib(default={})
    param_attributes = attr.ib(default={})


    logger = attr.ib(default=None)
    logger_name = attr.ib(default='ParameterFrame')
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

    def _generate_unique_id(self, txt : str) -> str:

        """
        Helper function to generate a unique ID for attribute entries
        """

        hash_id = hashlib.sha256(str(txt).encode()).hexdigest()
        return hash_id

    def process_parameters_from_files(self,
                           params_path : str = None,
                           param_names : dict = None,
                           param_descriptions : dict = None):

        """
        Process raw parameters from files.
        """

        if params_path is None:
            params_path = self.params_path

        if param_names is None:
            param_names = self.param_names

        if param_names is None:
            param_names = {os.path.basename(pp).split('.')[0] : os.path.join(params_path,pp) \
                for pp in os.listdir(params_path)}

        if param_descriptions is None:
            param_descriptions = self.param_descriptions

        if param_descriptions is None:
            param_descriptions = {pn : '' for pn in param_names}

        for param_name in param_names:

            self.param_attributes[param_name] = self.file_type_handler(
                file_path = param_names[param_name],
                parameter_name = param_name,
                parameter_description = param_descriptions[param_name]
            )

            self.param_attributes[param_name].process_file()

    def make_parameter_set(self,
                           parameter_set_name : str = None,
                           parameter_set_description : str = None,
                           parameter_names : list = None,
                           param_attributes : dict = None,
                           seed : int = None):

        """
        Use processed parameters to compose parameter set
        """

        if parameter_set_name is None:

            if seed is None:
                seed = self.seed
            parameter_set_name = self.name_generator.generate_random_name(seed = seed)

        if parameter_set_description is None:
            parameter_set_description = ''

        if param_attributes is None:
            param_attributes = self.param_attributes

        if parameter_names is None:
            parameter_names = [pn for pn in param_attributes]

        # generate parameter set id
        parameter_ids = [param_attributes[pa].parameter_id for pa in param_attributes]

        parameter_set_id = self._generate_unique_id(
            txt = ''.join(parameter_ids))

        # making parameter set lists
        parameter_set_description = [{'parameter_set_id' : parameter_set_id,
                               'parameter_set_name' : parameter_set_name,
                               'parameter_set_description' : parameter_set_description}]

        parameter_set = [{'parameter_set_id' : parameter_set_id,
                               'parameter_id' : parameter_id} for parameter_id in parameter_ids]

        # saving parameter set lists
        self.param_sets[parameter_set_name] = {'parameter_set' : parameter_set,
                                               'parameter_set_description' : parameter_set_description}


    def add_solution_description(self,
                                    solution_name : str,
                                    deployment_date : str = None,
                                    deprication_date : str = None,
                                    solution_description : str = None,
                                    solution_id : str = None,
                                    maintainers : list = None):

        """
        Add new solution description.
        """

        if solution_id is None:
            solution_id = self.solution_id

        # trim solution name
        solution_name = solution_name[:100]

        if solution_id is None:
            # if solution id not provided create new
            solution_id = self._generate_unique_id(
                txt = self.name_generator.generate_random_name() + solution_name)


        if solution_name not in self.solutions.keys():
            self.solutions[solution_name] = {}

        self.solutions[solution_name]['solution_description'] = {
            'solution_id' : solution_id,
            'solution_name' : solution_name,
            'solution_description' : solution_description,
            'deployment_date' : deployment_date,
            'deprication_date' : deprication_date,
            'maintainers' : maintainers
        }

    def _get_solution_name_from_memory(self, solution_id : str) -> str:

        """
        Get solution name from memory from solution id.
        """

        try:
            solution_name = [self.solutions[s]['solution_description']['solution_name'] \
                for s in self.solutions \
                    if self.solutions[s]['solution_description']['solution_id'] == solution_id][0]
        except Exception as e:
            raise ValueError(f"{solution_id} is not in solutions saved to memory!")

        return solution_name

    def _get_parameter_set_name_from_memory(self, parameter_set_id : str) -> str:

        """
        Get parameter set name from memory from parameter set id.
        """

        try:
            parameter_set_name = [self.param_sets[p]['parameter_set_description']['parameter_set_name'] \
                for p in self.param_sets \
                    if self.solutions[p]['parameter_set_description']['parameter_set_id'] == parameter_set_id][0]
        except Exception as e:
            raise ValueError(f"{parameter_set_id} is not in parameter sets saved to memory!")

        return parameter_set_name

    def _get_parameter_set_id_from_memory(self, parameter_set_name : str) -> str:

        """
        Get parameter set id from memory from parameter set name.
        """

        try:
            parameter_set_id = self.param_sets[parameter_set_name]['parameter_set_description']['parameter_set_id']

        except Exception as e:
            raise ValueError(f"{parameter_set_name} is not in parameter sets saved to memory!")

        return parameter_set_id


    def update_solution_description(self,
                                    solution_id : str,
                                    solution_name : str = None,
                                    deployment_date : str = None,
                                    deprication_date : str = None,
                                    solution_description : str = None,
                                    maintainers : list = None):

        """
        Update solution description.
        """

        # get solution name
        solution_name = self._get_solution_name_from_memory(solution_id = solution_id)

        # update description parameters
        if solution_name is not None:
            self.solutions[solution_name]['solution_description']['solution_name'] = solution_name
        if deployment_date is not None:
            self.solutions[solution_name]['solution_description']['deployment_date'] = deployment_date
        if deprication_date is not None:
            self.solutions[solution_name]['solution_description']['deprication_date'] = deprication_date
        if solution_description is not None:
            self.solutions[solution_name]['solution_description']['solution_description'] = solution_description
        if maintainers is not None:
            self.solutions[solution_name]['solution_description']['maintainers'] = maintainers


    def add_parameter_set_to_solution(self,
                            solution_id : str = None,
                            solution_name : str = None,
                            parameter_set_id : str = None,
                            parameter_set_name : str = None):

        """
        Add new solution description.
        """

        if solution_id is None:
            solution_id = self.solution_id

        if (solution_id is None) and (solution_name is None):
            raise ValueError("Provide either solution_id or solution_name!")

        if (parameter_set_id is None) and (parameter_set_name is None):
            raise ValueError("Provide either parameter_set_id or parameter_set_name!")

        if solution_name is None:
            solution_name = self._get_solution_name_from_memory(solution_id = solution_id)

        if (parameter_set_id is not None) and (parameter_set_name is None):
            parameter_set_name = self._get_parameter_set_name_from_memory(
                parameter_set_id = parameter_set_id)

        if (parameter_set_id is None) and (parameter_set_name is not None):
            parameter_set_id = self._get_parameter_set_id_from_memory(
                parameter_set_name = parameter_set_name)

        if solution_name not in self.solutions.keys():
            self.solutions[solution_name] = {}

        if 'solution_parameter_set' not in self.solutions[solution_name].keys():
            self.solutions[solution_name]['solution_parameter_set'] = {}

        self.solutions[solution_name]['solution_parameter_set'][parameter_set_name] = {
            'solution_id' : solution_id,
            'parameter_set_id' : parameter_set_id,
            'deployment_status' : "STAGING",
            'insertion_datetime' : datetime.now()
        }

    def _change_deployment_status(self,
                                 deployment_status : str,
                                 solution_id : str = None,
                                solution_name : str = None,
                                parameter_set_id : str = None,
                                parameter_set_name : str = None,
                                remote : bool = False):

        """
        Change deployment status of parameter set.
        """

        if solution_id is None:
            solution_id = self.solution_id

        if (solution_id is None) and (solution_name is None):
            raise ValueError("Provide either solution_id or solution_name!")

        if (parameter_set_id is None) and (parameter_set_name is None):
            raise ValueError("Provide either parameter_set_id or parameter_set_name!")

        if remote:
            raise Exception("Connection with parameter storage was not established!")
        else:

            if solution_name is None:
                solution_name = self._get_solution_name_from_memory(solution_id = solution_id)

            if (parameter_set_id is not None) and (parameter_set_name is None):
                parameter_set_name = self._get_parameter_set_name_from_memory(
                    parameter_set_id = parameter_set_id)

            if (parameter_set_id is None) and (parameter_set_name is not None):
                parameter_set_id = self._get_parameter_set_id_from_memory(
                    parameter_set_name = parameter_set_name)

            self.solutions[solution_name]['solution_parameter_set']\
                [parameter_set_name]['deployment_status'] = deployment_status

    def get_deployment_status(self,
                                 solution_id : str = None,
                                solution_name : str = None,
                                parameter_set_id : str = None,
                                parameter_set_name : str = None,
                                remote : bool = False):

        """
        Get deployment status of parameter set.
        """

        if solution_id is None:
            solution_id = self.solution_id

        if (solution_id is None) and (solution_name is None):
            raise ValueError("Provide either solution_id or solution_name!")

        if (parameter_set_id is None) and (parameter_set_name is None):
            raise ValueError("Provide either parameter_set_id or parameter_set_name!")

        if remote:
            raise Exception("Connection with parameter storage was not established!")
        else:

            if solution_name is None:
                solution_name = self._get_solution_name_from_memory(solution_id = solution_id)

            if (parameter_set_id is not None) and (parameter_set_name is None):
                parameter_set_name = self._get_parameter_set_name_from_memory(
                    parameter_set_id = parameter_set_id)

            if (parameter_set_id is None) and (parameter_set_name is not None):
                parameter_set_id = self._get_parameter_set_id_from_memory(
                    parameter_set_name = parameter_set_name)

            return self.solutions[solution_name]['solution_parameter_set']\
                [parameter_set_name]['deployment_status']

    def change_status_from_staging_to_production(self,
                                                 solution_id : str = None,
                                                solution_name : str = None,
                                                parameter_set_id : str = None,
                                                parameter_set_name : str = None,
                                                remote : bool = False):

        """
        Change deployment status of parameter set from staging to production.
        """

        current_deployment_status = self.get_deployment_status(
            solution_id = solution_id,
            solution_name = solution_name,
            parameter_set_id = parameter_set_id,
            parameter_set_name = parameter_set_name,
            remote = remote
        )

        if current_deployment_status != "STAGING":
            raise Exception(f"Current deployment status is {current_deployment_status}!")

        self._change_deployment_status(
            deployment_status = "PRODUCTION",
            solution_id = solution_id,
            solution_name = solution_name,
            parameter_set_id = parameter_set_id,
            parameter_set_name = parameter_set_name,
            remote = remote
        )

    def change_status_from_production_to_archived(self,
                                                 solution_id : str = None,
                                                solution_name : str = None,
                                                parameter_set_id : str = None,
                                                parameter_set_name : str = None,
                                                remote : bool = False):

        """
        Change deployment status of parameter set from production to archived.
        """

        current_deployment_status = self.get_deployment_status(
            solution_id = solution_id,
            solution_name = solution_name,
            parameter_set_id = parameter_set_id,
            parameter_set_name = parameter_set_name,
            remote = remote
        )

        if current_deployment_status != "PRODUCTION":
            raise Exception(f"Current deployment status is {current_deployment_status}!")

        self._change_deployment_status(
            deployment_status = "ARCHIVED",
            solution_id = solution_id,
            solution_name = solution_name,
            parameter_set_id = parameter_set_id,
            parameter_set_name = parameter_set_name,
            remote = remote
        )

