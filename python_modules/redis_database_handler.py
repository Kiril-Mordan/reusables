"""
Redis Database Handler

A handler class for managing interactions with a Redis database. This class provides methods for initializing a logger,
establishing a connection with the Redis server, performing CRUD operations, and searching within the stored data based on embeddings.
"""

# Imports
## essential
import logging
import json
import numpy as np
import attr
## requests
import redis
## embeddings
from sentence_transformers import SentenceTransformer

@attr.s
class RedisHandler:
    # pylint: disable=too-many-instance-attributes

    """
    A handler class for establishing and managing interactions with a Redis database.

    This class provides functionalities to connect to a Redis server, insert and retrieve data,
    and perform advanced operations like filtering keys based on specific criteria and searching
    the database with embeddings. It utilizes the sentence-transformers library for generating
    embeddings from text, which are then used in search operations.
    """

    # inputs with defaults
    embedder = attr.ib(default=SentenceTransformer('msmarco-distilbert-base-v4'))

    host = attr.ib(default="localhost", type=str)
    port = attr.ib(default=6379, type=int)
    db = attr.ib(default=0, type=int)

    logger = attr.ib(default=None)
    logger_name = attr.ib(default='Redis handler')
    loggerLvl = attr.ib(default=logging.INFO)

    # outputs
    client = attr.ib(default=None, init = False)
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
        Establishes a connection to the Redis server.
        """

        self.client = redis.Redis(host=self.host, port=self.port, db = self.db)

        try:
            if not self.client.ping():
                raise Exception("Connection to redis server was not established")

        except Exception as e:
            self.logger.error("Problem during connecting to Redis server!")
            print(e)

    def prepare_for_redis(self,data_dict):

        """
        Prepare a dictionary for storage in Redis by serializing all its values to strings.
        """


        def serialize_value(value):
            """
            Serialize a value to a JSON-compatible format.
            Handles standard types using JSON and ndarrays by conversion to lists.
            """
            if isinstance(value, np.ndarray):
                # Convert ndarray to list
                return json.dumps(value.tolist())
            elif isinstance(value, dict):
                # Recursively serialize dictionary
                return json.dumps({k: serialize_value(v) for k, v in value.items()})
            elif isinstance(value, (list, tuple)):
                # Convert lists and tuples to lists, then serialize
                return json.dumps([serialize_value(item) for item in value])
            else:
                # For standard types, use default serialization
                return json.dumps(value)


        serialized_dict = {}
        for key, value in data_dict.items():
            serialized_dict[key] = {}
            for subkey, subvalue in value.items():
                serialized_dict[key][subkey] = serialize_value(subvalue)
        return serialized_dict

    def decode_redis(self,data_dict):
        """
        Prepare a dictionary for storage in Redis by serializing all its values to strings.
        """
        serialized_dict = {}
        for key, value in data_dict.items():
            serialized_dict[key] = json.loads(value)
        return serialized_dict

    def insert_values_dict(self, values_dict):

        """
        Inserts key-value pairs into the Redis database.
        """

        try:

            values_dict = self.prepare_for_redis(values_dict)

            for key in values_dict:
                self.client.hset(key, mapping=values_dict[key])

        except Exception as e:
            self.logger.error("Problem during inserting list of key-values dictionaries into Redis database!")
            self.client.close()
            print(e)

    def flush_database(self):

        """
        Clears all keys in the current database.
        """

        try:
            self.client.flushall()

        except Exception as e:
            self.logger.error("Problem during flushing Redis database")
            self.client.close()
            print(e)

    def filter_keys(self, subkey = None, subvalue = None):

        """
        Filters keys in the Redis database based on specific criteria.
        """

        # initial keys filter
        filtered_keys = [key for key in self.client.keys() if self.client.type(key) == b'hash']
        # filtering keys in the HASH

        if (subkey is not None) and (subvalue is not None):
            self.keys_list = [key for key in filtered_keys if self.client.hmget(key, [subkey]) == [subvalue]]
        else:
            self.keys_list = filtered_keys

    def search_database_keys(self,
                        query : str,
                        similarity_metric,
                        search_results_n : int = 3) -> list:

        """
        Searches the database using embeddings and returns a list of keys that match the query.
        """

        # encoding search embedding
        try:
            query_embedding = self.embedder.encode(query).reshape(1, -1)

        except Exception as e:
            self.logger.error("Problem during embedding search query!")
            self.client.close()
            print(e)

        if self.keys_list is None:
            self.keys_list = [key for key in self.client.keys() if self.client.type(key) == b'hash']

        # extracting embeddings
        try:
            data_embeddings = np.array([json.loads(self.client.hmget(key, ['embedding'])[0]) for key in self.keys_list])

        except Exception as e:
            self.logger.error("Problem during extracting search pool embeddings!")
            self.client.close()
            print(e)

        # extracting results
        try:
            labels, _ = similarity_metric(query_embedding, data_embeddings, k=search_results_n)
            self.results_keys = [self.keys_list[i] for i in labels]

        except Exception as e:
            self.logger.error("Problem during extractinng results from the Redis database!")
            self.client.close()
            print(e)


    def get_dict_results(self, return_keys_list):

        """
        Retrieves specified fields from the search results in the Redis database.
        """

        results = [self.decode_redis(dict(zip(return_keys_list, self.client.hmget(searched_doc, return_keys_list)))) \
            for searched_doc in self.results_keys]

        return results