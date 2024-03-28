"""
Parameter frame

Parameter storage managing package, to push, pull and analize parameter sets.
"""

import attr
import os
import dill
import hashlib
from datetime import datetime
from mocker_db import MockerDB
import yaml
from collections import defaultdict
import logging

__design_choices__ = {
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


    def _process_yaml(self,
                     data : dict,
                     parent_id : str = None,
                     parameter_id : str = None) -> tuple:

        """
        Recursive function to process the YAML dictionary and turn it into list inputs.
        """

        parameter_attributes = []
        attribute_values = []

        for key, value in data.items():
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

                # It's a list, process each item
                parent_id = attribute_id
                for item in value:

                    attribute_id = self._generate_unique_id(str(item))

                    parameter_attributes.append({
                        'parameter_id' : parameter_id,
                        'attribute_id': attribute_id,
                        'previous_attribute_id': parent_id
                    })

                    attribute_values.append({
                        'attribute_id': attribute_id,
                        'attribute_name': key,
                        'attribute_value': item,
                        'attribute_value_type': type(item).__name__
                    })

        return parameter_attributes, attribute_values

    def _reconstruct_yaml(self,
                          parameter_attributes_list : list,
                          attribute_values_list : list):

        """
        Reconstructing yaml files from param and attribute lists.
        """

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
                return nested_attrs[attr_id]['value']

        # Start constructing the nested dictionary from the top-level attributes
        result = {}
        for attr in parameter_attributes_list:
            if attr['previous_attribute_id'] is None:
                # We are at a root attribute
                attr_name = id_to_name[attr['attribute_id']]
                result[attr_name] = construct_dict(attr['attribute_id'])

        return result

    def process_file(self, file_path : str = None):

        """
        Processes raw parameter file and prepares list of inputs for table handlers.
        """

        if file_path is None:
            file_path = self.file_path

        self.file_type = self._determine_file_type(file_path=file_path)
        self.file_content = self._load_file_content(file_path=file_path,
                                                               file_type=self.file_type)

        self.parameter_id = self._generate_unique_id(str(self.file_content))

        if self.file_type == 'yaml':
            (self.parameter_attributes_list,
             self.attribute_values_list) = self._process_yaml(data=self.file_content,
                                                              parameter_id=self.parameter_id)




    def reconstruct_file(self,
                         file_path : str = None,
                         parameter_attributes_list : list = None,
                         attribute_values_list : list = None):

        """
        Reconstructs raw file from pulled list from table handlers.
        """

        if file_path is None:
            file_path = self.file_path

        if parameter_attributes_list is None:
            parameter_attributes_list = self.parameter_attributes_list

        if attribute_values_list is None:
            attribute_values_list = self.attribute_values_list

        self.file_type = self._determine_file_type(file_path=file_path)

        if self.file_type == 'yaml':
            self.file_content = self._reconstruct_yaml(attribute_values_list=attribute_values_list,
                                             parameter_attributes_list=parameter_attributes_list)

            # Write the dictionary to a YAML file
            with open(file_path, 'w', encoding='utf-8') as file:
                yaml.dump(self.file_content, file, sort_keys=False)







@attr.s
class ParameterFrame:

    params_path = attr.ib()
    list_of_params = attr.ib(default=None, type=list)

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
