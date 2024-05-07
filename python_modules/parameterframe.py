"""
Parameterframe

The module provides an interface for managing solution parameters.
It allows for the structured storage and retrieval of parameter sets from a database.
"""

import attr
import os
import random
import dill
import hashlib
from datetime import datetime
from mocker_db import MockerDB, MockerConnector #==0.1.1
import yaml
from collections import defaultdict
import logging
import ast

from sqlalchemy import create_engine, Column, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship, sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, DBAPIError
from sqlalchemy import inspect


__design_choices__ = {
    "FileTypeHandler" : ['prepares one parameter file and reconstructs one parameter file at a time',
                         'txt and yaml files can be processed',
                         'yaml files are not reconstructed 1to1 but are first make into python dictionary, with python type mapping'],
    "ParameterFrame" : ['parameter_names and paramer_description are optional'],
    "DatabaseConnector" : ['connector is an external component that includes handling of connection to some database',
                           'default connector is meant for MockerDB',
                           'any other database connector has to expose add_entries, modify_entries, remove_entries, get_entries, commit',
                           'entries are supplied in a list of dictionaries with name of the table',
                           'connector is to be initialized and supplied externally']
}


# Metadata for package creation
__package_metadata__ = {
    "author": "Kyrylo Mordan",
    "author_email": "parachute.repo@gmail.com",
    "description": "A tool to manage parameters in a form of files, process them, upload to param storage, pull and reconstrut as files.",
    "keywords" : ['python', 'parameter storage']
}

@attr.s
class MockerDatabaseConnector:

    db_handler = attr.ib(default=MockerDB)
    db_remote_handler = attr.ib(default=MockerConnector)
    db_handler_params = attr.ib(default = {
        'file_path' : "./parameterframe_storage",
         'persist' : True})
    connection_details = attr.ib(default = {
        'base_url' : "http://localhost:8000"})
    logger = attr.ib(default=None)
    logger_name = attr.ib(default='Mocker Database Connector')
    loggerLvl = attr.ib(default=logging.INFO)
    logger_format = attr.ib(default=None)


    def __attrs_post_init__(self):
        self._initialize_logger()
        self._initialize_mocker()

    def _initialize_logger(self):

        """
        Initialize a logger for the class instance based on the specified logging level and logger name.
        """

        if self.logger is None:
            logging.basicConfig(level=self.loggerLvl, format=self.logger_format)
            logger = logging.getLogger(self.logger_name)
            logger.setLevel(self.loggerLvl)

            self.logger = logger

    def _initialize_mocker(self):

        self.db_handler = self.db_handler(**self.db_handler_params)


    def add_entries(self, table_name: str, entries : list) -> bool:
        try:

            processed_entries = [{**item, 'table_name': table_name} for item in entries]

            self.db_handler.insert_values(values_dict_list = processed_entries,
                                                var_for_embedding_name = '',
                                                embed = False)

        except Exception as e:
            self.logger.error(f"Failed to add entries: {e}")
            return False

        return True

    def fetch_entries(self,
                      filters : dict = None,
                      database_name : str = 'default'):

        """
        Fetches entries from remove mocker to local mocker
        """

        db_remote_handler = self.db_remote_handler(**self.connection_details)

        fetched_data = db_remote_handler.search_data(
            database_name = database_name,
            filter_criteria = filters)

        self.db_handler.insert_values(
            values_dict_list = fetched_data['results'],
            embed = False)

        return True

    def remove_entries(self,
                       filters : dict = None,
                       database_name : str = 'default'):

        """
        Removes entries from remote and local mocker
        """

        db_remote_handler = self.db_remote_handler(**self.connection_details)

        db_remote_handler.delete_data(
            database_name = database_name,
            filter_criteria = filters)

        self.db_handler.remove_from_database(
            filter_criteria = filters)

        return True


    def get_entries(self,
                    table_name: str,
                    return_keys : list = None,
                    filters : dict = None ) -> list:
        try:

            if filters is None:
                filters = {}
            filters['table_name'] = table_name

            result_entries = self.db_handler.search_database(
                filter_criteria = filters,
                return_keys_list = return_keys)

            result_entries = [{k: v for k, v in item.items() if k != 'table_name'} \
                for item in result_entries]

        except Exception as e:
            self.logger.error(f"Failed to add entries: {e}")
            return False

        return result_entries

    def commit(self):

        db_remote_handler = self.db_remote_handler(**self.connection_details)

        db_remote_handler.insert_data(
            data = [d for _, d in self.db_handler.data.items()]
        )

        return True

    def push_tables(self,
                      solution_description : list = None,
                      solution_parameter_set : list = None,
                      parameter_set : list = None,
                      parameter_set_description : list = None,
                      parameter_description : list = None,
                      parameter_attribute : list = None,
                      attribute_values : list = None):

        """
        Pushes tables with database handler
        """

        if solution_description:
            self.add_entries(table_name = 'solution_description',
                                                entries = solution_description)
        if solution_parameter_set:
            self.add_entries(table_name = 'solution_parameter_set',
                                                entries = solution_parameter_set)
        if parameter_set:
            self.add_entries(table_name = 'parameter_set',
                                                entries = parameter_set)
        if parameter_set_description:
            self.add_entries(table_name = 'parameter_set_description',
                                                entries = parameter_set_description)
        if parameter_description:
            self.add_entries(table_name = 'parameter_description',
                                                entries = parameter_description)
        if parameter_attribute:
            self.add_entries(table_name = 'parameter_attribute',
                                                entries = parameter_attribute)
        if attribute_values:
            self.add_entries(table_name = 'attribute_values',
                                                entries = attribute_values)

        self.commit()

        return True

    def pull_tables(self,
                      solution_id : str = None,
                      parameter_set_id : str = None):

        """
        Pulls commited tables from database for selected solutions
        """

        if solution_id is None:
            raise ValueError("Provide solution_id!")

        fetch_filters = {'table_name' : ['solution_description',
                                          'solution_parameter_set',
                                          'parameter_set',
                                          'parameter_set_description'],
                          'solution_id': [solution_id, None]}

        if parameter_set_id:
            fetch_filters['parameter_set_id'] = [parameter_set_id, None]

        # fetch tables with solution and parameter_set_ids
        self.fetch_entries(
            filters = fetch_filters)

        # get parameter_id for fetching next tables
        dict_param_ids = self.get_entries(
            table_name = 'parameter_set',
            return_keys=['parameter_id'])

        param_ids = [dict_param_id['parameter_id'] for dict_param_id in dict_param_ids]

        # fetch tables with parameter_ids
        self.fetch_entries(
            filters={'table_name' : ['parameter_description',
                                          'parameter_attribute'],
                          'parameter_id': param_ids})

        # get attribute_ids for fetching next tables
        dict_attribute_ids = self.get_entries(
            table_name = 'parameter_attribute',
            return_keys=['attribute_id'])

        attribute_ids = [dict_attribute_id['attribute_id'] \
            for dict_attribute_id in dict_attribute_ids]

        # fetch final tables
        self.fetch_entries(
            filters={'table_name' : 'attribute_values',
                          'attribute_id': attribute_ids})

        # get table lists from connector
        solution_description = self.get_entries(
    table_name = 'solution_description')
        solution_parameter_sets = self.get_entries(
    table_name = 'solution_parameter_set')
        parameter_sets = self.get_entries(
    table_name = 'parameter_set')
        parameter_set_descriptions = self.get_entries(
    table_name = 'parameter_set_description')
        parameter_descriptions = self.get_entries(
    table_name = 'parameter_description')
        parameter_attributes = self.get_entries(
    table_name = 'parameter_attribute')
        attribute_values = self.get_entries(
    table_name = 'attribute_values')

        return (
            solution_description,
            solution_parameter_sets,
            parameter_sets,
            parameter_set_descriptions,
            parameter_descriptions,
            parameter_attributes,
            attribute_values
        )

    def get_parameter_sets_info(self,
                            solution_id : str = None,
                            parameter_set_ids : list = None,
                            deployment_status : str = None):

        """
        Get parameter sets for solution id with select deployment status.
        """

        if solution_id is None:
            raise ValueError("Provide solution_id!")


        fetch_filters = {'table_name' : 'solution_parameter_set',
                        'solution_id': solution_id}

        get_filters = {'solution_id': solution_id}

        if parameter_set_ids:
            fetch_filters['parameter_set_id'] = parameter_set_ids
            get_filters['parameter_set_id'] = parameter_set_ids

        if deployment_status:
            fetch_filters['deployment_status'] = deployment_status
            get_filters['deployment_status'] = deployment_status

        # fetch tables with solution and parameter_set_ids

        self.fetch_entries(
            filters=fetch_filters)

        solution_parameter_sets = self.get_entries(
            table_name = 'solution_parameter_set',
            filters=get_filters)


        return solution_parameter_sets

    def modify_parameter_set_status(self,
                                    solution_id : str,
                                    parameter_set_ids : list,
                                    current_deployment_status : str,
                                    new_deployment_status : str):

        """
        Reuploads solution parameter set entry with different status
        """

        solution_parameter_sets = self.get_parameter_sets_info(
            solution_id = solution_id,
            parameter_set_ids = parameter_set_ids,
            deployment_status = current_deployment_status
        )

        if len(solution_parameter_sets) == 0:
            self.logger.warning(f"No deployed parameter_set_ids with {current_deployment_status} from selected!")
            return False

        for solution_parameter_set in solution_parameter_sets:

            self.remove_entries(
                filters = {'table_name' : 'solution_parameter_set',
                        'solution_id': solution_parameter_set['solution_id'],
                        'parameter_set_id' : solution_parameter_set['parameter_set_id'],
                        'deployment_status' : current_deployment_status}
            )
            solution_parameter_set['deployment_status'] = new_deployment_status

            self.logger.info(
                f"{solution_id} + {solution_parameter_set['parameter_set_id']} : {current_deployment_status} -> {new_deployment_status}")

        return self.push_tables(solution_parameter_set = solution_parameter_sets)




@attr.s
class SqlAlchemyDatabaseManager:


    connection_details = attr.ib(default = {
        'base_url' : "http://localhost:8000"})

    _instance = None
    Base = declarative_base()

    logger = attr.ib(default=None)
    logger_name = attr.ib(default='SqlAlchemy Database Connector')
    loggerLvl = attr.ib(default=logging.INFO)
    logger_format = attr.ib(default=None)


    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SqlAlchemyDatabaseManager, cls).__new__(cls)
        return cls._instance

    def __attrs_post_init__(self):

        if not hasattr(self, 'engine'):
            self.engine = create_engine(self.connection_details['base_url'])
            self.Session = sessionmaker(bind=self.engine)

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

    class AttributeValues(Base):
        __tablename__ = 'attribute_values'
        attribute_id = Column(String, primary_key=True)
        previous_attribute_id = Column(String, nullable=True)
        attribute_name = Column(String)
        attribute_value = Column(String)
        attribute_value_type = Column(String)

    class ParameterDescription(Base):
        __tablename__ = 'parameter_description'
        parameter_id = Column(String, primary_key=True)
        parameter_name = Column(String)
        parameter_description = Column(Text)
        file_name = Column(String)
        file_type = Column(String)

    class ParameterAttribute(Base):
        __tablename__ = 'parameter_attribute'
        parameter_id = Column(String, ForeignKey('parameter_description.parameter_id'), primary_key=True)
        attribute_id = Column(String, ForeignKey('attribute_values.attribute_id'), primary_key=True)
        previous_attribute_id = Column(String, nullable=True)
        attribute_values = relationship("AttributeValues")
        parameter_description = relationship("ParameterDescription")

    class ParameterSet(Base):
        __tablename__ = 'parameter_set'
        parameter_set_id = Column(String, primary_key=True)
        parameter_id = Column(String,primary_key=True)
        #parameter_description = relationship("ParameterDescription")
        # If ParameterAttribute should be related here, it needs adjustment.

    class SolutionParameterSet(Base):
        __tablename__ = 'solution_parameter_set'
        solution_id = Column(String, primary_key=True)
        parameter_set_id = Column(String, primary_key=True)
        #parameter_set = relationship("ParameterSet")
        deployment_status = Column(String)
        insertion_datetime = Column(String)


    class ParameterSetDescription(Base):
        __tablename__ = 'parameter_set_description'
        parameter_set_id = Column(String, primary_key=True)
        parameter_set_name = Column(String)
        parameter_set_description = Column(Text)
        # This should not have parameter_id as primary key if it's not part of ParameterSet primary key.

    class SolutionDescription(Base):
        __tablename__ = 'solution_description'
        solution_id = Column(String, primary_key=True)
        solution_name = Column(String)
        solution_description = Column(Text)
        deployment_date = Column(String)
        deprecation_date = Column(String, nullable=True)
        maintainers = Column(Text)

    # Define other models similarly

    def create_tables(self):
        self.Base.metadata.create_all(self.engine)

    def drop_tables(self):
        self.Base.metadata.drop_all(self.engine)


    def _merge_entries(self, entries):
        with self.Session() as session:
            try:
                for entry in entries:
                    session.merge(entry)  # Merges based on primary key
                session.commit()
            except SQLAlchemyError as e:
                session.rollback()
                self.logger.error(f"SQLAlchemy Error: {e}")


    def _as_dict(self, obj, with_relationships=False):
        data = {c.key: getattr(obj, c.key) for c in inspect(obj).mapper.column_attrs}
        if with_relationships:
            for relationship in inspect(obj).mapper.relationships:
                related_data = getattr(obj, relationship.key)
                if related_data is not None:
                    if isinstance(related_data, list):
                        data[relationship.key] = [self._as_dict(child, True) for child in related_data]
                    else:
                        data[relationship.key] = self._as_dict(related_data, True)
        return data

    def push_tables(self,
                      solution_description : list = None,
                      solution_parameter_set : list = None,
                      parameter_set : list = None,
                      parameter_set_description : list = None,
                      parameter_description : list = None,
                      parameter_attribute : list = None,
                      attribute_values : list = None):

        """
        Pushes tables with database handler
        """

        inserts = []

        if solution_description:
            solution_description = [self.SolutionDescription(**data)
                                    for data in solution_description]
            inserts += solution_description
        if parameter_description:
            parameter_description = [self.ParameterDescription(**data)
                                    for data in parameter_description]
            inserts += parameter_description
        if parameter_set_description:
            parameter_set_description = [self.ParameterSetDescription(**data)
                                    for data in parameter_set_description]
            inserts += parameter_set_description
        if solution_parameter_set:
            solution_parameter_set = [self.SolutionParameterSet(**data)
                                    for data in solution_parameter_set]
            inserts += solution_parameter_set
        if parameter_set:
            parameter_set = [self.ParameterSet(**data)
                                    for data in parameter_set]
            inserts += parameter_set
        if parameter_attribute:
            parameter_attribute = [self.ParameterAttribute(**data)
                                    for data in parameter_attribute]
            inserts += parameter_attribute
        if attribute_values:
            attribute_values = [self.AttributeValues(**data)
                                    for data in attribute_values]
            inserts += attribute_values

        if inserts:
            self._merge_entries(entries = inserts)
            return True

        return False

    def pull_tables(self,
                    solution_id : str = None,
                    parameter_set_id : str = None):

        """
        Pulls commited tables from database for selected solutions
        """

        if solution_id is None:
            raise ValueError("Provide solution_id!")

        session = self.Session()
        try:
            # Fetch related entries based on solution_id and parameter_set_id
            solution_descriptions = session.query(self.SolutionDescription).filter(
                self.SolutionDescription.solution_id == solution_id).all()
            if parameter_set_id:
                solution_parameter_sets = session.query(self.SolutionParameterSet).filter(
                    self.SolutionParameterSet.solution_id == solution_id,
                    self.SolutionParameterSet.parameter_set_id == parameter_set_id).all()
                parameter_sets = session.query(self.ParameterSet).filter(
                    self.ParameterSet.parameter_set_id == parameter_set_id).all()
                parameter_set_descriptions = session.query(self.ParameterSetDescription).filter(
                    self.ParameterSetDescription.parameter_set_id == parameter_set_id).all()
            else:
                solution_parameter_sets = session.query(self.SolutionParameterSet).filter(
                    self.SolutionParameterSet.solution_id == solution_id).all()

                parameter_set_ids = [solution_parameter_set.parameter_set_id for solution_parameter_set in solution_parameter_sets]

                parameter_sets = session.query(self.ParameterSet).filter(
                    self.ParameterSet.parameter_set_id.in_(parameter_set_ids)).all()
                parameter_set_descriptions = session.query(self.ParameterSetDescription).filter(
                    self.ParameterSetDescription.parameter_set_id.in_(parameter_set_ids)).all()

            # Fetch parameter_id from parameter_sets for further queries
            param_ids = [param.parameter_id for param in parameter_sets]

            # Continue to fetch related entries based on parameter_id
            parameter_descriptions = session.query(self.ParameterDescription).filter(
                self.ParameterDescription.parameter_id.in_(param_ids)).all()
            parameter_attributes = session.query(self.ParameterAttribute).filter(
                self.ParameterAttribute.parameter_id.in_(param_ids)).all()

            # Get attribute_ids for fetching attribute values
            attribute_ids = [attr.attribute_id for attr in parameter_attributes]
            attribute_values = session.query(self.AttributeValues).filter(
                self.AttributeValues.attribute_id.in_(attribute_ids)).all()

            return (
                [self._as_dict(data) for data in solution_descriptions],
                [self._as_dict(data) for data in solution_parameter_sets],
                [self._as_dict(data) for data in parameter_sets],
                [self._as_dict(data) for data in parameter_set_descriptions],
                [self._as_dict(data) for data in parameter_descriptions],
                [self._as_dict(data) for data in parameter_attributes],
                [self._as_dict(data) for data in attribute_values]
            )

        except Exception as e:
            session.rollback()
            print(f"An error occurred: {e}")
        finally:
            session.close()

    def get_parameter_sets_info(self,
                            solution_id : str = None,
                            parameter_set_ids : list = None,
                            deployment_status : str = None):

        """
        Get parameter sets for solution id with select deployment status.
        """

        if solution_id is None:
            raise ValueError("Provide solution_id!")

        session = self.Session()
        try:
            if parameter_set_ids :
                solution_parameter_sets = session.query(self.SolutionParameterSet).filter(
                    self.SolutionParameterSet.solution_id == solution_id,
                    self.SolutionParameterSet.parameter_set_id == parameter_set_ids).all()
            elif parameter_set_ids and deployment_status:
                solution_parameter_sets = session.query(self.SolutionParameterSet).filter(
                    self.SolutionParameterSet.solution_id == solution_id,
                    self.SolutionParameterSet.parameter_set_id == parameter_set_ids,
                    self.SolutionParameterSet.deployment_status == deployment_status).all()
            else:
                solution_parameter_sets = session.query(self.SolutionParameterSet).filter(
                    self.SolutionParameterSet.solution_id == solution_id,
                    self.SolutionParameterSet.deployment_status == deployment_status).all()

            return [self._as_dict(data) for data in solution_parameter_sets]

        except Exception as e:
            session.rollback()
            print(f"An error occurred: {e}")
        finally:
            session.close()

    def modify_parameter_set_status(self,
                                    solution_id : str,
                                    parameter_set_ids : list,
                                    current_deployment_status : str,
                                    new_deployment_status : str):

        """
        Reuploads solution parameter set entry with different status
        """

        solution_parameter_sets = self.get_parameter_sets_info(
            solution_id = solution_id,
            parameter_set_ids = parameter_set_ids,
            deployment_status = current_deployment_status
        )

        if len(solution_parameter_sets) == 0:
            self.logger.warning(f"No deployed parameter_set_ids with {current_deployment_status} from selected!")
            return False


        session = self.Session()
        parameter_set_ids = [t['parameter_set_id'] for t in solution_parameter_sets]
        try:
            # Fetch the user record to modify
            solution_parameter_sets = session.query(self.SolutionParameterSet).filter(
                self.SolutionParameterSet.solution_id == solution_id,
                self.SolutionParameterSet.parameter_set_id.in_(parameter_set_ids),
                self.SolutionParameterSet.deployment_status == current_deployment_status).all()

            if solution_parameter_sets:
                for solution_parameter_set in solution_parameter_sets:
                    solution_parameter_set.deployment_status = new_deployment_status
                    self.logger.info(
        f"{solution_id} + {solution_parameter_set.parameter_set_id} : {current_deployment_status} -> {new_deployment_status}")
                    session.commit()



        except Exception as e:
            session.rollback()  # Roll back in case of errors
            print(f"An error occurred: {e}")
        finally:
            session.close()  # Close the session to free resources


        return True


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

    is_reconstructed = attr.ib(default=False, type = bool)
    # types for which fth will work
    available_types = attr.ib(default=['yaml', 'txt' ,'other'])
    chunk_size = attr.ib(default=255)

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
        # if file_extension == '.dill':
        #     return 'dill'

        return 'other'

    def _load_file_content(self,
                            file_path: str,
                            file_type : str) -> object:

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
            # elif file_type == 'dill':
            #     with open(file_path, 'rb') as file:
            #         content = dill.load(file)
            #     return content
            else:
                # Fallback or additional file types can be handled here
                with open(file_path, 'rb') as file:
                    content = file.read()
                return content
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
                     parameter_id : str = None,
                     chunk_size: int = None) -> tuple:

        """
        Function to process txt files.
        """

        if chunk_size is None:
            chunk_size = self.chunk_size

        parameter_attributes = []
        attribute_values = []

        # Split the text into chunks of chunk_size
        for i in range(0, len(content), chunk_size):
            chunk = content[i:i+chunk_size]
            attribute_id = self._generate_unique_id(chunk)

            parameter_attributes.append({
                'parameter_id': parameter_id,
                'attribute_id': attribute_id,
                # Assuming each chunk is sequential and does not have a 'parent' as in a tree structure
                'previous_attribute_id': None if i == 0 else parameter_attributes[-1]['attribute_id']
            })

            attribute_values.append({
                'attribute_id': attribute_id,
                'attribute_name': f'{int(i//chunk_size)}',
                'attribute_value': str(chunk),
                'attribute_value_type': type(content).__name__
            })

        return parameter_attributes, attribute_values

    def _encode_obj(self, data : object) -> str:
        """Encode data using Dill."""
        encoded_bytes = dill.dumps(data) #base64.b64encode(data.encode('utf-8'))
        return encoded_bytes#.decode('utf-8')

    def _decode_obj(self, encoded_data : object) -> object:
        """Decode data from serialized object."""
        decoded_bytes = dill.loads(encoded_data)
        return decoded_bytes

    def _encode_binary(self, data : str) -> str:
        """Encode data using Base64."""
        return str(data)

    def _decode_binary(self, encoded_data : str) -> str:
        """Decode data from Base64."""
        return ast.literal_eval(encoded_data)


    def _process_dill(self,
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
            'attribute_value': self._encode_obj(data = content),
            'attribute_value_type': type(content).__name__
        }]

        return parameter_attributes, attribute_values

    def _process_binary(self,
                     content : dict,
                     parameter_id : str = None,
                     chunk_size: int = None) -> tuple:

        """
        Function to process txt files.
        """


        if chunk_size is None:
            chunk_size = self.chunk_size

        parameter_attributes = []
        attribute_values = []

        str_content = str(content)

        # Split the text into chunks of chunk_size
        for i in range(0, len(str_content), chunk_size):
            chunk = str_content[i:i+chunk_size]
            attribute_id = self._generate_unique_id(chunk)

            parameter_attributes.append({
                'parameter_id': parameter_id,
                'attribute_id': attribute_id,
                # Assuming each chunk is sequential and does not have a 'parent' as in a tree structure
                'previous_attribute_id': None if i == 0 else parameter_attributes[-1]['attribute_id']
            })

            attribute_values.append({
                'attribute_id': attribute_id,
                'attribute_name': f'{int(i//chunk_size)}',
                'attribute_value': self._encode_binary(data = chunk),
            'attribute_value_type': type(content).__name__
            })

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
                          attribute_values_list : list) -> object:

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
                         attribute_values_list : list) -> object:

        """
        Reconstructing txt files from param and attribute lists.
        """

        try:
            # Assuming each attribute_value in attribute_values_list contains 'attribute_id', 'attribute_name', and 'attribute_value'

            # Sort the attribute_values_list by attribute_name to ensure the correct order
            # Assuming attribute_name has been stored as 'chunk_X' where X is a sequence number
            sorted_attributes = sorted(attribute_values_list, key=lambda x: int(x['attribute_name']))

            # Reconstruct the text by concatenating the 'attribute_value' of each sorted attribute
            reconstructed_text = ''.join(attr['attribute_value'] for attr in sorted_attributes)

        except Exception as e:
            raise Exception("Failure to reconstruct text!", e)

        return reconstructed_text

    def _reconstruct_dill(self,
                         attribute_values_list : list) -> object:

        """
        Reconstructing txt files from param and attribute lists.
        """

        return self._decode_obj(encoded_data = attribute_values_list[0]['attribute_value'])

    def _reconstruct_binary(self,
                         attribute_values_list : list) -> object:

        """
        Reconstructing txt files from param and attribute lists.
        """

        try:
            # Assuming each attribute_value in attribute_values_list contains 'attribute_id', 'attribute_name', and 'attribute_value'

            # Sort the attribute_values_list by attribute_name to ensure the correct order
            # Assuming attribute_name has been stored as 'chunk_X' where X is a sequence number
            sorted_attributes = sorted(attribute_values_list, key=lambda x: int(x['attribute_name']))

            # Reconstruct the text by concatenating the 'attribute_value' of each sorted attribute
            reconstructed_binary = ''.join(attr['attribute_value'] for attr in sorted_attributes)

        except Exception as e:
            raise Exception("Failure to reconstruct binary!", e)

        return self._decode_binary(encoded_data = reconstructed_binary)

    def _process_file(self,
                      file_content : dict,
                      file_type : str,
                      parameter_id : str) -> tuple:

        """
        Process file of predefined type
        """

        if file_type == 'yaml':
            return self._process_yaml(content = file_content,
                                    parameter_id = parameter_id)

        if file_type == 'txt':
            return self._process_txt(content = file_content,
                                    parameter_id = parameter_id)

        if file_type == 'dill':
            return self._process_dill(content = file_content,
                                        parameter_id = parameter_id)

        if file_type == 'other':
            return self._process_binary(content = file_content,
                                        parameter_id = parameter_id)


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


        (self.parameter_attributes_list,
            self.attribute_values_list) = self._process_file(file_content = self.file_content,
                                                            file_type = self.file_type,
                                                            parameter_id = self.parameter_id)

    def _reconstruct_file_content(self,
                          file_type : str,
                          attribute_values_list : list,
                          parameter_attributes_list : list = None) -> object:

        """
        Reconstructs file content from lists
        """

        if file_type == 'yaml':
            return self._reconstruct_yaml(attribute_values_list = attribute_values_list,
                                                        parameter_attributes_list = parameter_attributes_list)

        if file_type == 'txt':
            return self._reconstruct_txt(attribute_values_list = attribute_values_list)

        if file_type == 'dill':
            return self._reconstruct_dill(attribute_values_list = attribute_values_list)

        if file_type == 'other':
            return self._reconstruct_binary(attribute_values_list = attribute_values_list)

        return None


    def _reconstruct_file(self,
                          file_path : str,
                          file_type : str,
                          file_content : object) -> bool:

        """
        Reconstructs file from file content
        """

        if file_type == 'yaml':
            # Write the dictionary to a YAML file
            with open(file_path, 'w', encoding='utf-8') as file:
                yaml.dump(file_content, file, sort_keys=False)

            return True

        if file_type == 'txt':

            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(file_content)

            return True

        if file_type == 'dill':

            with open(file_path, 'wb') as file:
                dill.dump(file_content, file)

            return True

        if file_type == 'other':

            with open(file_path, 'wb') as file:
                file.write(file_content)

            return True

        return False



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

        if self.file_type not in self.available_types:
            raise ValueError(f"File type is {self.file_type}!")

        # selecting subset for specific parameter_id
        (parameter_attributes_list,
         attribute_values_list) = self._prefilter_search_lists(
             parameter_id = parameter_id,
             parameter_attributes_list = parameter_attributes_list,
             attribute_values_list = attribute_values_list
         )

        self.file_content = self._reconstruct_file_content(
                          file_type = self.file_type,
                          attribute_values_list = attribute_values_list,
                          parameter_attributes_list = parameter_attributes_list)

        self.is_reconstructed = self._reconstruct_file(
                          file_path = file_path,
                          file_type = self.file_type,
                          file_content = self.file_content)


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

        if seed is None:
            seed = self.seed

        if isinstance(seed, int):
            # Set the seed value
            random.seed(seed)
            self.seed += 1

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

    params_path = attr.ib(default=None)

    # optional
    solution_id = attr.ib(default=None, type=str)
    param_names = attr.ib(default=None, type=dict)
    param_descriptions = attr.ib(default=None, type=dict)
    seed = attr.ib(default=None, type=int)

    connection_details = attr.ib(default = {
        'base_url' : "http://localhost:8000"})

    # dependancies
    database_connector = attr.ib(default=None, type=MockerDatabaseConnector)
    file_type_handler = attr.ib(default=FileTypeHandler)
    name_generator = attr.ib(default=ComplexNameGenerator)

    # inner
    seed = attr.ib(default=23, type=int)
    solutions = attr.ib(default={})
    param_sets = attr.ib(default={})
    param_attributes = attr.ib(default={})

    commited_tables = attr.ib(default={})


    logger = attr.ib(default=None)
    logger_name = attr.ib(default='ParameterFrame')
    loggerLvl = attr.ib(default=logging.INFO)
    logger_format = attr.ib(default=None)


    def __attrs_post_init__(self):
        self._initialize_logger()

        if self.database_connector is None:
            self.database_connector = MockerDatabaseConnector(connection_details = self.connection_details)

        self._initialize_name_generator()

        import pandas as pd

        self.pd = pd
        self.pd.set_option('display.max_colwidth', 70)

        self.solutions = {}
        self.param_sets = {}
        self.commited_tables = {}
        self.param_attributes = {}


    def _initialize_logger(self):

        """
        Initialize a logger for the class instance based on the specified logging level and logger name.
        """

        if self.logger is None:
            logging.basicConfig(level=self.loggerLvl, format=self.logger_format)
            logger = logging.getLogger(self.logger_name)
            logger.setLevel(self.loggerLvl)

            self.logger = logger

    def _initialize_name_generator(self):

        """
        Initializing name generator
        """

        self.name_generator = self.name_generator(seed = self.seed)

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

        return True

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
            parameter_set_name = self.name_generator.generate_random_name()

        if parameter_set_description is None:
            parameter_set_description = ''

        if param_attributes is None:
            param_attributes = self.param_attributes

        if parameter_names is None:
            parameter_names = [pn for pn in param_attributes]

        # generate parameter set id
        parameter_ids = [param_attributes[pa].parameter_id for pa in parameter_names]

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

        self.logger.info(f"Parameter set id for {parameter_set_name}: {parameter_set_id}")


    def add_solution(self,
                        solution_name : str,
                        deployment_date : str = None,
                        deprecation_date : str = None,
                        solution_description : str = None,
                        solution_id : str = None,
                        maintainers : list = None,
                        seed : int = None):

        """
        Add new solution and its description.
        """

        if seed is None:
            seed = self.seed

        # trim solution name
        solution_name = solution_name[:100]

        if solution_id is None:
            # if solution id not provided create new
            solution_id = self._generate_unique_id(
                txt = self.name_generator.generate_random_name(seed = seed) \
                    + solution_name)

        if solution_name not in self.solutions.keys():
            self.solutions[solution_name] = {}

        if 'solution_id' not in self.solutions[solution_name].keys():
            self.solutions[solution_name]['solution_id'] = solution_id

        self.solutions[solution_name]['solution_description'] = {
            'solution_id' : solution_id,
            'solution_name' : solution_name,
            'solution_description' : solution_description,
            'deployment_date' : deployment_date,
            'deprecation_date' : deprecation_date,
            'maintainers' : maintainers
        }

        self.logger.info(f"Solution id for {solution_name}: {solution_id}")
        return True



    def _get_solution_name_from_memory(self, solution_id : str) -> str:

        """
        Get solution name from memory from solution id.
        """

        try:
            solution_name = [self.solutions[s]['solution_id'] \
                for s in self.solutions \
                    if self.solutions[s]['solution_id'] == solution_id][0]
        except Exception as e:
            self.logger.warning(f"{solution_id} is not in solutions saved to memory!")
            solution_name = self.name_generator.generate_random_name()
            self.logger.warning(f"Name {solution_name} is assigned to {solution_id} temporarily!")


        return solution_name

    def _get_parameter_set_name_from_memory(self, parameter_set_id : str) -> str:

        """
        Get parameter set name from memory from parameter set id.
        """

        try:
            parameter_set_name = [self.param_sets[p]['parameter_set_description'][-1]['parameter_set_name'] \
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
            parameter_set_id = self.param_sets[parameter_set_name]['parameter_set_description'][-1]['parameter_set_id']

        except Exception as e:
            raise ValueError(f"{parameter_set_name} is not in parameter sets saved to memory!")

        return parameter_set_id


    def update_solution_description(self,
                                    solution_id : str,
                                    solution_name : str = None,
                                    deployment_date : str = None,
                                    deprecation_date : str = None,
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
        if deprecation_date is not None:
            self.solutions[solution_name]['solution_description']['deprecation_date'] = deprecation_date
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
        Add parameter set to solution
        """

        if solution_id is None:
            solution_id = self.solution_id

        if (solution_id is None) and (solution_name is None):
            raise ValueError("Provide either solution_id or solution_name!")

        if solution_id is None:
            solution_id = self.solutions[solution_name]['solution_id']

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

        if 'solution_id' not in self.solutions[solution_name].keys():
            self.solutions[solution_name]['solution_id'] = solution_id

        if 'solution_parameter_set' not in self.solutions[solution_name].keys():
            self.solutions[solution_name]['solution_parameter_set'] = {}

        self.solutions[solution_name]['solution_parameter_set'][parameter_set_name] = {
            'solution_id' : solution_id,
            'parameter_set_id' : parameter_set_id,
            'deployment_status' : "STAGING",
            'insertion_datetime' : datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        return True

    def commit_solution(self,
                        solution_id : str = None,
                        solution_name : str = None,
                        parameter_set_ids : list = None,
                        parameter_set_names : list = None):

        """
        Commit solution to local store.
        """

        if solution_id is None:
            solution_id = self.solution_id

        if (solution_id is None) and (solution_name is None):
            raise ValueError("Provide either solution_id or solution_name!")

        if solution_id is None:
            solution_id = self.solutions[solution_name]['solution_id']

        if solution_name is None:
            solution_name = self._get_solution_name_from_memory(solution_id = solution_id)


        # save solution with param set
        if solution_id not in self.commited_tables.keys():
            self.commited_tables[solution_id] = {}

        solution_description = None
        if 'solution_description' in self.solutions[solution_name].keys():
            solution_description = [self.solutions[solution_name]['solution_description']]

        ## save solution description
        self.commited_tables[solution_id]= {
            'solution_description' : solution_description,
            'solution_parameter_set' : {},
            'parameter_set' : {},
            'parameter_set_description' : {},
            'parameter_description' : {},
            'parameter_attribute' : {},
            'attribute_values' : {}
        }

        if solution_description:
            self.logger.info(f"Commited solution description for {solution_id}")

        if (parameter_set_ids is not None) or (parameter_set_names is not None):

            if (parameter_set_ids is not None) and (parameter_set_names is None):
                    parameter_set_names = [self._get_parameter_set_name_from_memory(
                        parameter_set_id = parameter_set_id) \
                            for parameter_set_id in parameter_set_ids]

            if (parameter_set_ids is None) and (parameter_set_names is not None):
                parameter_set_ids = [self._get_parameter_set_id_from_memory(
                    parameter_set_name = parameter_set_name) \
                        for parameter_set_name in parameter_set_names]

            if (parameter_set_ids is None) and (parameter_set_names is None):
                    raise ValueError("Provide either parameter_set_ids or parameter_set_names!")


            for parameter_set_id, parameter_set_name in zip(parameter_set_ids, parameter_set_names):

                ## save to solution_parameter_set
                self.commited_tables[solution_id]['solution_parameter_set'][parameter_set_id] = \
                    [self.solutions[solution_name]['solution_parameter_set'][parameter_set_name]]
                ## save to parameter_set
                self.commited_tables[solution_id]['parameter_set'][parameter_set_id] = \
                    self.param_sets[parameter_set_name]['parameter_set']
                ## save to parameter_set_description
                self.commited_tables[solution_id]['parameter_set_description'][parameter_set_id] = \
                    self.param_sets[parameter_set_name]['parameter_set_description']
                ## save to parameter_description
                for parameter_set in self.param_sets[parameter_set_name]['parameter_set']:

                    parameter_id = parameter_set['parameter_id']

                    parameter_name = [self.param_attributes[param_name].parameter_name \
                        for param_name in self.param_attributes \
                            if self.param_attributes[param_name].parameter_id == parameter_id][0]

                    # saving parameter descriptions
                    if parameter_set_id not in self.commited_tables[solution_id]['parameter_description'].keys():
                        self.commited_tables[solution_id]['parameter_description'][parameter_set_id] = {}
                    self.commited_tables[solution_id]['parameter_description'][parameter_set_id][parameter_id] = \
                        self.param_attributes[parameter_name].parameter_description

                    # saving parameter attributes list
                    if parameter_set_id not in self.commited_tables[solution_id]['parameter_attribute'].keys():
                        self.commited_tables[solution_id]['parameter_attribute'][parameter_set_id] = {}
                    self.commited_tables[solution_id]['parameter_attribute'][parameter_set_id][parameter_id] = \
                        self.param_attributes[parameter_name].parameter_attributes_list

                    # saving attribute values
                    if parameter_set_id not in self.commited_tables[solution_id]['attribute_values'].keys():
                        self.commited_tables[solution_id]['attribute_values'][parameter_set_id] = {}
                    self.commited_tables[solution_id]['attribute_values'][parameter_set_id][parameter_id] = \
                        self.param_attributes[parameter_name].attribute_values_list

                self.logger.info(f"Commited solution tables for {solution_id}")

        return True

    def _prep_ps_for_reconstruction(self,
                                 solution_id : str,
                                 parameter_set_id : str) -> tuple:

        """
        Prepares data for reconstruction from selected solutio and param set ids.
        """

        parameter_ids = [ps['parameter_id'] \
            for ps in self.commited_tables[solution_id]['parameter_set'][parameter_set_id]]

        parameter_description = self.commited_tables[solution_id]['parameter_description'][parameter_set_id]

        ### param_id_paths
        param_id_paths = {param_id : parameter_description[param_id][0]['file_name'] for param_id in parameter_ids}

        ### attribute_values
        attribute_values_list = []

        attribute_values_dict = self.commited_tables[solution_id]['attribute_values'][parameter_set_id]

        for parameter_id in attribute_values_dict:

            if parameter_id in parameter_ids:
                attribute_values_list += attribute_values_dict[parameter_id]

        ### parameter_attribute
        parameter_attribute_list = []

        parameter_attribute_dict = self.commited_tables[solution_id]['parameter_attribute'][parameter_set_id]

        for parameter_id in parameter_attribute_dict:

            if parameter_id in parameter_ids:
                parameter_attribute_list += parameter_attribute_dict[parameter_id]



        return param_id_paths, attribute_values_list, parameter_attribute_list

    def _reconstruct_ps(self,
                      parameter_attribute_list : list,
                      attribute_values_list : list,
                      param_id_paths : dict,
                      params_path : str):

        """
        Reconstructs selected parameter set
        """

        for param_id in param_id_paths:

            file_name = param_id_paths[param_id]
            file_path = os.path.join(params_path, file_name)

            fth = self.file_type_handler(
                        file_path = file_path,
                        parameter_id = param_id,
                        parameter_attributes_list = parameter_attribute_list,
                        attribute_values_list = attribute_values_list
                    )
            fth.reconstruct_file()


        return True

    def reconstruct_parameter_set(self,
                                  solution_id : str  = None,
                                  parameter_set_id : str = None,
                                  solution_name : str = None,
                                  parameter_set_name : str = None,
                                  params_path : str = None):

        """
        Reconstructs selected parameter set
        """

        if (solution_id is None) and (solution_name is None):
            raise ValueError("Provide either solution_id or solution_name!")

        if (parameter_set_id is None) and (parameter_set_name is None):
            raise ValueError("Provide either parameter_set_id or parameter_set_name!")

        if solution_id is None:
            solution_id = [id for id, dd in self.commited_tables.items() \
                if dd['solution_description'][0]['solution_name'] == solution_name][0]

        if parameter_set_id is None:
            parameter_set_id = [id for id, dd in self.commited_tables[solution_id]['parameter_set_description'].items() \
                if dd[0]['parameter_set_name'] == parameter_set_name][0]

        # prepare for reconstruction
        (param_id_paths,
        attribute_values_list,
        parameter_attribute_list) = self._prep_ps_for_reconstruction(
            solution_id = solution_id,
            parameter_set_id = parameter_set_id
        )

        self._reconstruct_ps(
            parameter_attribute_list = parameter_attribute_list,
            attribute_values_list = attribute_values_list,
            param_id_paths = param_id_paths,
            params_path = params_path
        )

    def _prep_tables_for_pushing(self,
                                 solution_id : str,
                                 parameter_set_ids : list = None):

        """
        Prepare tables for pushing selected solution
        """

        solution_parameter_set = []
        parameter_set = []
        parameter_set_description = []
        parameter_description = []
        parameter_attribute = []
        attribute_values = []

        try:

            solution_description = self.commited_tables[solution_id]['solution_description']
            ##

            if parameter_set_ids:
                for parameter_set_id in parameter_set_ids:

                    solution_parameter_set = solution_parameter_set + \
                        self.commited_tables[solution_id]['solution_parameter_set'][parameter_set_id]
                    parameter_set = parameter_set + \
                        self.commited_tables[solution_id]['parameter_set'][parameter_set_id]
                    parameter_set_description = parameter_set_description + \
                        self.commited_tables[solution_id]['parameter_set_description'][parameter_set_id]

                    parameter_description_dict = self.commited_tables[solution_id]['parameter_description'][parameter_set_id]
                    parameter_description = parameter_description + \
                        [item for sublist in parameter_description_dict.values() for item in sublist]

                    parameter_attribute_dict = self.commited_tables[solution_id]['parameter_attribute'][parameter_set_id]
                    parameter_attribute = parameter_attribute + \
                        [item for sublist in parameter_attribute_dict.values() for item in sublist]

                    attribute_values_dict = self.commited_tables[solution_id]['attribute_values'][parameter_set_id]
                    attribute_values = attribute_values + \
                        [item for sublist in attribute_values_dict.values() for item in sublist]

                    return (solution_description,
                            solution_parameter_set,
                            parameter_set,
                            parameter_set_description,
                            parameter_description,
                            parameter_attribute,
                            attribute_values)

        except Exception as e:
            self.logger.error("Problem during preparation of tables for pushing!")
            raise e

        return solution_description

    def push_solution(self,
                      solution_id : list = None,
                      solution_name : list = None,
                      parameter_set_ids : list = None,
                      parameter_set_names : list = None,):

        """
        Pushes commited tables to database handler for selected solutions
        """

        if (solution_id is None) and (solution_name is None):
            raise ValueError("Provide either solution_ids or solution_names!")

        if solution_id is None:
            solution_id = [id for id, dd in self.commited_tables.items() \
                if dd['solution_description'][0]['solution_name'] == solution_name][0]

        if (parameter_set_ids is None) and (parameter_set_names is None):
            solution_description = self._prep_tables_for_pushing(
                solution_id = solution_id
            )

            self.database_connector.push_tables(
                solution_description = solution_description
            )

            return True


        if parameter_set_ids is None:
            parameter_set_ids = [id for id, dd in self.commited_tables[solution_id]['parameter_set_description'].items() \
                if dd[0]['parameter_set_name'] in parameter_set_names]


        (solution_description,
            solution_parameter_set,
            parameter_set,
            parameter_set_description,
            parameter_description,
            parameter_attribute,
            attribute_values) = self._prep_tables_for_pushing(
                solution_id = solution_id,
                parameter_set_ids = parameter_set_ids
            )

        self.database_connector.push_tables(

            solution_description = solution_description,
            solution_parameter_set = solution_parameter_set,
            parameter_set = parameter_set,
            parameter_set_description = parameter_set_description,
            parameter_description = parameter_description,
            parameter_attribute = parameter_attribute,
            attribute_values = attribute_values
        )

        return True

    def _rebuild_tables_from_pulled_data(self,
                                     solution_id: str,
                                     parameter_set_ids: list,
                                     solution_description,
                                     solution_parameter_sets,
                                     parameter_sets,
                                     parameter_set_descriptions,
                                     parameter_descriptions,
                                     parameter_attributes,
                                     attribute_values):
        """
        Rebuild the committed_tables dictionary structure from the flat lists
        returned by the `_prep_tables_for_pushing` function. This function
        distributes list elements evenly across provided parameter_set_ids.
        """

        try:
            # Initialize the main dictionary for the solution_id
            if solution_id not in self.commited_tables:
                self.commited_tables[solution_id] = {}

            # Set the solution description
            self.commited_tables[solution_id]['solution_description'] = solution_description

            # Initialize dictionaries for this solution_id
            if 'solution_parameter_set' not in self.commited_tables[solution_id].keys():
                self.commited_tables[solution_id]['solution_parameter_set'] = {}
            if 'parameter_set' not in self.commited_tables[solution_id].keys():
                self.commited_tables[solution_id]['parameter_set'] = {}
            if 'parameter_set_description' not in self.commited_tables[solution_id].keys():
                self.commited_tables[solution_id]['parameter_set_description'] = {}
            if 'parameter_description' not in self.commited_tables[solution_id].keys():
                self.commited_tables[solution_id]['parameter_description'] = {}
            if 'parameter_attribute' not in self.commited_tables[solution_id].keys():
                self.commited_tables[solution_id]['parameter_attribute'] = {}
            if 'attribute_values' not in self.commited_tables[solution_id].keys():
                self.commited_tables[solution_id]['attribute_values'] = {}

            # Calculate distribution counts for each list based on the number of parameter_set_ids
            num_ids = len(parameter_set_ids)
            sps_count = len(solution_parameter_sets)
            ps_count = len(parameter_sets)
            psd_count = len(parameter_set_descriptions)
            pd_count = len(parameter_descriptions)
            # pa_count = len(parameter_attributes) // num_ids
            # av_count = len(attribute_values) // num_ids

            # Iterators for each type of data
            sps_iter = iter(solution_parameter_sets)
            ps_iter = iter(parameter_sets)
            psd_iter = iter(parameter_set_descriptions)
            pd_iter = iter(parameter_descriptions)
            # pa_iter = iter(parameter_attributes)
            # av_iter = iter(attribute_values)

            for parameter_set_id in parameter_set_ids:
                # Distribute solution_parameter_sets
                self.commited_tables[solution_id]['solution_parameter_set'][parameter_set_id] = [next(sps_iter) for _ in range(sps_count)]

                # Distribute parameter_sets
                self.commited_tables[solution_id]['parameter_set'][parameter_set_id] = [next(ps_iter) for _ in range(ps_count)]

                # Distribute parameter_set_descriptions
                self.commited_tables[solution_id]['parameter_set_description'][parameter_set_id] = [next(psd_iter) for _ in range(psd_count)]

                # Distribute parameter_descriptions
                parameter_descriptions = [next(pd_iter) for _ in range(pd_count)]
                self.commited_tables[solution_id]['parameter_description'][parameter_set_id] = {
                    parameter_description['parameter_id'] : [parameter_description] \
                        for parameter_description in parameter_descriptions}

                parameter_ids = [parameter_description['parameter_id'] \
                    for parameter_description in parameter_descriptions]

                if parameter_set_id not in self.commited_tables[solution_id]['parameter_attribute'].keys():
                    self.commited_tables[solution_id]['parameter_attribute'][parameter_set_id] = {}

                if parameter_set_id not in self.commited_tables[solution_id]['attribute_values'].keys():
                    self.commited_tables[solution_id]['attribute_values'][parameter_set_id] = {}

                for parameter_id in parameter_ids:

                    # Distribute parameter_attributes
                    self.commited_tables[solution_id]['parameter_attribute'][parameter_set_id][parameter_id] = [
                        parameter_attribute for parameter_attribute in parameter_attributes \
                            if parameter_attribute['parameter_id'] == parameter_id]

                    attribute_ids = [parameter_attribute['attribute_id'] \
                        for parameter_attribute in parameter_attributes \
                            if parameter_attribute['parameter_id'] == parameter_id]

                    # Distribute attribute_values
                    self.commited_tables[solution_id]['attribute_values'][parameter_set_id][parameter_id] = [
                        attribute_value for attribute_value in attribute_values \
                            if attribute_value['attribute_id'] in attribute_ids]

        except Exception as e:
            self.logger.error("Problem during rebuilding of tables from pushed data!")
            raise e



    def pull_solution(self,
                      solution_id : str = None,
                      parameter_set_id : str = None):

        """
        Pulls commited tables from database for selected solutions
        """

        if solution_id is None:
            raise ValueError("Provide solution_id!")


        (solution_description,
         solution_parameter_sets,
         parameter_sets,
         parameter_set_descriptions,
         parameter_descriptions,
         parameter_attributes,
         attribute_values) = self.database_connector.pull_tables(
            solution_id = solution_id,
            parameter_set_id = parameter_set_id
        )

        if len(solution_description) == 0:
            self.logger.warning(f"No solutions with {solution_id} could be pulled!")

        parameter_set_ids = [solution_parameter_set['parameter_set_id'] for solution_parameter_set in solution_parameter_sets]

        if len(parameter_set_ids) == 0:
            self.logger.warning(f"No parameter sets were pulled for solution_id {solution_id}")

        # get table lists into commited
        self._rebuild_tables_from_pulled_data(
            solution_id = solution_id,
            parameter_set_ids = parameter_set_ids,
            solution_description = solution_description,
            solution_parameter_sets = solution_parameter_sets,
            parameter_sets = parameter_sets,
            parameter_set_descriptions = parameter_set_descriptions,
            parameter_descriptions = parameter_descriptions,
            parameter_attributes = parameter_attributes,
            attribute_values = attribute_values
        )

        return True

    def _change_deployment_status(self,
                                 deployment_status : str,
                                 solution_id : str = None,
                                solution_name : str = None,
                                parameter_set_id : str = None,
                                parameter_set_name : str = None,
                                remote : bool = True):

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

    def get_parameter_set_id_for_solution(self,
                                          solution_id : str = None,
                                          deployment_status : str = None):

        """
        Get parameter set id/s for solution id with select deployment status.
        """

        tabs = self.database_connector.get_parameter_sets_info(
            solution_id=solution_id,
            deployment_status=deployment_status)

        parameter_set_ids = [t['parameter_set_id'] for t in tabs]

        return parameter_set_ids

    def get_deployment_status(self,
                                 solution_id : str = None,
                                parameter_set_id : str = None):

        """
        Get deployment status of parameter set.
        """

        tabs = self.database_connector.get_parameter_sets_info(
            solution_id=solution_id,
            parameter_set_ids=parameter_set_id)

        return [t['deployment_status'] for t in tabs][0]


    def change_status_from_staging_to_production(self,
                                                 solution_id : str = None,
                                                parameter_set_id : str = None):

        """
        Change deployment status of parameter set from staging to production.
        """

        self.database_connector.modify_parameter_set_status(
                solution_id=solution_id,
                parameter_set_ids = parameter_set_id,
                current_deployment_status = "STAGING",
                new_deployment_status = "PRODUCTION"
            )


    def change_status_from_production_to_archived(self,
                                                 solution_id : str = None,
                                                parameter_set_id : str = None):

        """
        Change deployment status of parameter set from production to archived.
        """

        self.database_connector.modify_parameter_set_status(
                solution_id=solution_id,
                parameter_set_ids = parameter_set_id,
                current_deployment_status = "PRODUCTION",
                new_deployment_status = "ARCHIVED"
            )


    def change_status_from_archived_production(self,
                                                solution_id : str = None,
                                                parameter_set_id : str = None):

        """
        Change deployment status of parameter set from archived to production.
        """

        self.database_connector.modify_parameter_set_status(
                solution_id=solution_id,
                parameter_set_ids = None,
                current_deployment_status = "PRODUCTION",
                new_deployment_status = "STAGING"
            )

        self.database_connector.modify_parameter_set_status(
                solution_id=solution_id,
                parameter_set_ids = parameter_set_id,
                current_deployment_status = "ARCHIVED",
                new_deployment_status = "PRODUCTION"
            )

    def show_solutions(self):

        """
        Show info on locally commited solutions
        """

        solution_descriptions = [self.commited_tables[sid]['solution_description'][0] \
             if self.commited_tables[sid]['solution_description'] else {'solution_id' : sid} for sid in self.commited_tables]

        for solution_description in solution_descriptions:

            if 'solution_name' not in solution_description.keys():
                solution_description['solution_name'] = None
                solution_description['solution_description'] = None
                solution_description['deployment_date'] = None
                solution_description['deprecation_date'] = None
                solution_description['maintainers'] = None


        solution_descriptions_pd = self.pd.DataFrame(solution_descriptions)

        if solution_descriptions_pd.shape[0] == 0:
            solution_descriptions_pd['solution_id'] = [sid for sid in self.commited_tables]
            solution_descriptions_pd['solution_name'] = [None for sid in self.commited_tables]
            solution_descriptions_pd['solution_description'] = [None for sid in self.commited_tables]
            solution_descriptions_pd['deployment_date'] = [None for sid in self.commited_tables]
            solution_descriptions_pd['deprecation_date'] = [None for sid in self.commited_tables]
            solution_descriptions_pd['maintainers'] = [None for sid in self.commited_tables]

        solution_descriptions_pd['commited_parameter_sets'] = [
                    len(self.commited_tables[sid]['solution_parameter_set']) \
                    if self.commited_tables[sid]['solution_parameter_set'] != {}\
                    else 0
                    for sid in self.commited_tables
                ]

        return solution_descriptions_pd

    def show_parameter_sets(self, solution_id : str):

        """
        Show info on locally commited parameter_sets for solution_id
        """


        solution_parameter_sets = [
            sps for spsid in self.commited_tables[solution_id]['solution_parameter_set'] \
                for sps in self.commited_tables[solution_id]['solution_parameter_set'][spsid]]
        solution_parameter_sets_pd = self.pd.DataFrame(solution_parameter_sets)

        if solution_parameter_sets_pd.shape[0] == 0:
            raise ValueError(f"Solution with id {solution_id} does not exist locally!")

        solution_parameter_sets_pd = solution_parameter_sets_pd.drop(columns=["solution_id"])

        parameter_set_descriptions = [
            sps for spsid in self.commited_tables[solution_id]['parameter_set_description'] \
                for sps in self.commited_tables[solution_id]['parameter_set_description'][spsid]]
        parameter_set_descriptions_pd = self.pd.DataFrame(parameter_set_descriptions)


        psdsp_id_pd = parameter_set_descriptions_pd.merge(
            solution_parameter_sets_pd, on = 'parameter_set_id')
        psdsp_id_pd['commited_parameters'] = [
            len(self.commited_tables[solution_id]['parameter_set'][pid_d['parameter_set_id']]) \
                for pid_d in parameter_set_descriptions]

        return psdsp_id_pd

    def show_parameters(self, solution_id : str, parameter_set_id : str):

        """
        Show info on locally commited parameters for solution_id and parameter_set_id
        """

        if parameter_set_id not in self.commited_tables[solution_id]['parameter_description']:
            raise ValueError(f"Parameter set with id {parameter_set_id} does not exist locally for solution {solution_id}!")

        parameter_descriptions = self.commited_tables[solution_id]['parameter_description'][parameter_set_id]
        parameter_descriptions_l = [parameter_descriptions[pid][0] for pid in parameter_descriptions]
        parameter_descriptions_pd = self.pd.DataFrame(parameter_descriptions_l)
        parameter_descriptions_pd['commited_attributes'] = [
            len(self.commited_tables[solution_id]['parameter_attribute'][parameter_set_id][parameter_id]) \
                for parameter_id in parameter_descriptions]
        return parameter_descriptions_pd





