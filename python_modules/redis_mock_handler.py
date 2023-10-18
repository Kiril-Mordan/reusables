"""
Redis Mock Handler

A mock handler class for simulating interactions with a Redis database, using local file storage.
This class provides methods for initializing a logger, establishing a connection by loading data from a file,
saving data back to a file, performing CRUD operations, and searching within the stored data based on embeddings.
"""

# Imports
## essential
import numpy as np
import dill
import attr
import logging
## embeddings
from sentence_transformers import SentenceTransformer


@attr.s
class RedisMockHandler:

    # inputs with defaults
    embedder = attr.ib(default=SentenceTransformer('msmarco-distilbert-base-v4'))

    file_path = attr.ib(default="../DATA/reviews_backup", type=str)

    logger = attr.ib(default=None)
    logger_name = attr.ib(default='Mock handler')
    loggerLvl = attr.ib(default=logging.INFO)

    # outputs
    data = attr.ib(default=None, init=False)

    def __attrs_post_init__(self):
        self.initialize_logger()

    def initialize_logger(self):
        if self.logger is None:
            logging.basicConfig(level=self.loggerLvl)
            logger = logging.getLogger(self.logger_name)
            logger.setLevel(self.loggerLvl)

            self.logger = logger

    def establish_connection(self):
        try:
            with open(self.file_path, 'rb') as file:
                self.data = dill.load(file)
        except FileNotFoundError:
            self.data = []
        except Exception as e:
            self.logger.error("Error loading data from file: ", e)

    def save_data(self):
        try:
            with open(self.file_path, 'wb') as file:
                dill.dump(self.data, file)
        except Exception as e:
            self.logger.error("Error saving data to file: ", e)

    def insert_values_dict(self, values_dict):
        try:
            self.data.append(values_dict)
            self.save_data()
        except Exception as e:
            self.logger.error("Problem during inserting list of key-values dictionaries into mock database!", e)

    def flush_database(self):
        try:
            self.data = []
            self.save_data()
        except Exception as e:
            self.logger.error("Problem during flushing mock database", e)

    def filter_keys(self, subkey=None, subvalue=None):
        if (subkey is not None) and (subvalue is not None):
            self.keys_list = [d for d in self.data if self.data[d][subkey] == subvalue.decode('utf-8')]
        else:
            self.keys_list = self.data

    def search_database_keys(self, query: str, similarity_metric, search_results_n: int = 3) -> list:
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
        # This method mimics the behavior of the original 'get_dict_results' method
        results = []
        for searched_doc in self.results_keys:
            result = {key: self.data[searched_doc].get(key) for key in return_keys_list}
            results.append(result)
        return results

