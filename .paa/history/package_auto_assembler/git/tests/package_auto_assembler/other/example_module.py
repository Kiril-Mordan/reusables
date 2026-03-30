"""
Mock Vector Db Handler

This class is a mock handler for simulating a vector database, designed primarily for testing and development scenarios.
It offers functionalities such as text embedding, hierarchical navigable small world (HNSW) search,
and basic data management within a simulated environment resembling a vector database.
"""

# Imports
## essential
import logging
import json
import time
import attr #>=22.2.0
from .dependancies.example_local_dependacy_2 import *
from .dependancies.bundle_1.dep_from_bundle_1 import *

#! import sklearn #==1.5.1 
#! import sklearn 
#! import numpy 
#! import torch #<=2.4.1
#! import fastapi #[all]


# Metadata for package creation
__package_metadata__ = {
    "author": "Kyrylo Mordan",
    "author_email": "parachute.repo@gmail.com",
    "version": "0.0.1",
    "description": "A mock handler for simulating a vector database.",
    "keywords" : ['python', 'vector database', 'similarity search']
    # Add other metadata as needed
}


@attr.s
class MockVecDbHandler:
    # pylint: disable=too-many-instance-attributes

    """
    The MockVecDbHandler class simulates a vector database environment, primarily for testing and development purposes.
    It integrates various functionalities such as text embedding, Hierarchical Navigable Small World (HNSW) search,
    and basic data management, mimicking operations in a real vector database.

    Parameters:
        embeddings_url (str): URL to access OpenAI models for generating embeddings, crucial for text analysis.
        godID (str): Unique identifier for authentication with the embedding service.
        headers (dict): HTTP headers for API interactions with the embedding service.
        file_path (str): Local file path for storing and simulating the database; defaults to "../redis_mock".
        persist (bool): Flag to persist data changes; defaults to False.
        embedder_error_tolerance (float): Tolerance level for embedding errors; defaults to 0.0.
        logger (logging.Logger): Logger instance for activity logging.
        logger_name (str): Name for the logger; defaults to 'Mock handler'.
        loggerLvl (int): Logging level, set to logging.INFO by default.
        return_keys_list (list): Fields to return in search results; defaults to an empty list.
        search_results_n (int): Number of results to return in searches; defaults to 3.
        similarity_search_type (str): Type of similarity search to use; defaults to 'hnsw'.
        similarity_params (dict): Parameters for similarity search; defaults to {'space':'cosine'}.

    Attributes:
        data (dict): In-memory representation of database contents.
        filtered_data (dict): Stores filtered database entries based on criteria.
        keys_list (list): List of keys in the database.
        results_keys (list): Keys matching specific search criteria.

    Methods:
        initialize_logger()
            Sets up logging for the class instance.

        hnsw_search(search_emb, doc_embs, k=1, space='cosine', ef_search=50, M=16, ef_construction=200)
            Performs HNSW algorithm-based search.

        linear_search(search_emb, doc_embs, k=1, space='cosine')
            Conducts a linear search.

        establish_connection(file_path=None)
            Simulates establishing a database connection.

        save_data()
            Saves the current state of the 'data' attribute to a file.

        embed(text)
            Generates embeddings for text inputs.

        _prepare_for_redis(data_dict, var_for_embedding_name)
            Prepares data for storage in Redis.

        insert_values_dict(values_dict, var_for_embedding_name)
            Simulates insertion of key-value pairs into the database.

        flush_database()
            Clears all data in the mock database.

        filter_keys(subkey=None, subvalue=None)
            Filters data entries based on a specific subkey and subvalue.

        filter_database(filter_criteria=None)
            Filters a dictionary based on multiple field criteria.

        remove_from_database(filter_criteria=None)
            Removes key-value pairs from a dictionary based on filter criteria.

        search_database_keys(query, search_results_n=None, similarity_search_type=None, similarity_params=None)
            Searches the database using embeddings and saves a list of entries that match the query.

        get_dict_results(return_keys_list=None)
            Retrieves specified fields from the search results.

        search_database(query, search_results_n=None, filter_criteria=None, similarity_search_type=None,
                        similarity_params=None, return_keys_list=None)
            Searches and retrieves fields from the database for a given filter.
    """

    ## for accessing openAI models
    embeddings_url = attr.ib(default=None)
    godID = attr.ib(default=None)
    headers = attr.ib(default=None)

    ## for embeddings
    model_type = attr.ib(default='sentence_transformer', type=str)
    st_model_name = attr.ib(default='all-MiniLM-L6-v2', type=str)
    st_model = attr.ib(default=None, init=False)


    ## for similarity search
    return_keys_list = attr.ib(default=[], type = list)
    search_results_n = attr.ib(default=3, type = int)
    similarity_search_type = attr.ib(default='linear', type = str)
    similarity_params = attr.ib(default={'space':'cosine'}, type = dict)

    ## inputs with defaults
    file_path = attr.ib(default="../redis_mock", type=str)
    persist = attr.ib(default=False, type=bool)

    embedder_error_tolerance = attr.ib(default=0.0, type=float)

    logger = attr.ib(default=None)
    logger_name = attr.ib(default='Mock handler')
    loggerLvl = attr.ib(default=logging.INFO)
    logger_format = attr.ib(default=None)

    ## outputs
    data = attr.ib(default=None, init=False)
    filtered_data = attr.ib(default=None, init=False)
    keys_list = attr.ib(default=None, init = False)
    results_keys = attr.ib(default=None, init = False)

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

