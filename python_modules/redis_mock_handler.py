"""
Redis Mock Handler

A mock handler class for simulating interactions with a Redis database, using local file storage.
This class provides methods for initializing a logger, establishing a connection by loading data from a file,
saving data back to a file, performing CRUD operations, and searching within the stored data based on embeddings.
"""

# Imports
## essential
import logging
import numpy as np
import dill
import attr
## embeddings
from sentence_transformers import SentenceTransformer


@attr.s
class RedisMockHandler:
    # pylint: disable=too-many-instance-attributes

    """
    Redis Mock Handler

    A mock handler class for simulating interactions with a Redis database, using local file storage.
    This class provides methods for initializing a logger, establishing a connection by loading data from a file,
    saving data back to a file, performing CRUD operations, and searching within the stored data based on embeddings.
    """

    # inputs with defaults
    embedder = attr.ib(default=SentenceTransformer('msmarco-distilbert-base-v4'))

    file_path = attr.ib(default="../DATA/reviews_backup", type=str)

    logger = attr.ib(default=None)
    logger_name = attr.ib(default='Mock handler')
    loggerLvl = attr.ib(default=logging.INFO)

    # outputs
    data = attr.ib(default=None, init=False)
    keys_list = attr.ib(default=None, init = False)
    results_keys = attr.ib(default=None, init = False)

    def __attrs_post_init__(self):
        self.initialize_logger()

    def initialize_logger(self):

        """
        Initialize a logger for the class instance based on the specified logging level and logger name.
        """

        if self.logger is None:
            logging.basicConfig(level=self.loggerLvl)
            logger = logging.getLogger(self.logger_name)
            logger.setLevel(self.loggerLvl)

            self.logger = logger

    def establish_connection(self):

        """
        Simulates establishing a connection by loading data from a local file into the 'data' attribute.
        """

        try:
            with open(self.file_path, 'rb') as file:
                self.data = dill.load(file)
        except FileNotFoundError:
            self.data = []
        except Exception as e:
            self.logger.error("Error loading data from file: ", e)

    def save_data(self):

        """
        Saves the current state of 'data' back into a local file.
        """

        try:
            with open(self.file_path, 'wb') as file:
                dill.dump(self.data, file)
        except Exception as e:
            self.logger.error("Error saving data to file: ", e)

    def insert_values_dict(self, values_dict):

        """
        Simulates inserting key-value pairs into the mock Redis database.
        """

        try:
            self.data.append(values_dict)
            self.save_data()
        except Exception as e:
            self.logger.error("Problem during inserting list of key-values dictionaries into mock database!", e)

    def flush_database(self):

        """
        Clears all data in the mock database.
        """

        try:
            self.data = []
            self.save_data()
        except Exception as e:
            self.logger.error("Problem during flushing mock database", e)

    def filter_keys(self, subkey=None, subvalue=None):

        """
        Filters data entries based on a specific subkey and subvalue.
        """

        if (subkey is not None) and (subvalue is not None):
            self.keys_list = [d for d in self.data if self.data[d][subkey] == subvalue.decode('utf-8')]
        else:
            self.keys_list = self.data

    def search_database_keys(self, query: str, similarity_metric, search_results_n: int = 3) -> list:

        """
        Searches the mock database using embeddings and returns a list of entries that match the query.
        """

        try:
            query_embedding = self.embedder.encode(query).reshape(1, -1)
        except Exception as e:
            self.logger.error("Problem during embedding search query!", e)

        if self.keys_list is None:
            self.keys_list = [key for key in self.data]

        try:
            data_embeddings = np.array([eval(self.data[d]['embedding']) for d in self.keys_list])
        except Exception as e:
            self.logger.error("Problem during extracting search pool embeddings!", e)

        # self.logger.info(self.keys_list)
        # self.logger.info(data_embeddings)

        try:
            labels, _ = similarity_metric(query_embedding, data_embeddings, k=search_results_n)
            self.results_keys = [self.keys_list[i] for i in labels]
        except Exception as e:
            self.logger.error("Problem during extracting results from the mock database!", e)

    def get_dict_results(self, return_keys_list):

        """
        Retrieves specified fields from the search results in the mock database.
        """

        # This method mimics the behavior of the original 'get_dict_results' method
        results = []
        for searched_doc in self.results_keys:
            result = {key: self.data[searched_doc].get(key) for key in return_keys_list}
            results.append(result)
        return results
