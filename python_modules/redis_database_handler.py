"""
Redis Database Handler

A handler class for managing interactions with a Redis database. This class provides methods for initializing a logger,
establishing a connection with the Redis server, performing CRUD operations, and searching within the stored data based on embeddings.
"""


# Imports
## essential
import numpy as np
import attr
import logging
# ## switching path to main lvl
# sys.path.append(os.path.dirname(sys.path[0]))
## requests
import redis
## embeddings
from sentence_transformers import SentenceTransformer

@attr.s
class RedisHandler:

    # inputs with defaults
    embedder = attr.ib(default=SentenceTransformer('msmarco-distilbert-base-v4'))

    host = attr.ib(default="localhost", type=str)
    port = attr.ib(default=6379, type=int)
    db = attr.ib(default=0, type=int)

    logger = attr.ib(default=None)
    logger_name = attr.ib(default='Redis handler')
    loggerLvl = attr.ib(default=logging.INFO)

    # outputs
    conn = attr.ib(default=None, init = False)

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

        self.client = redis.Redis(host=self.host, port=self.port, db = self.db)

        try:
            if not self.client.ping():
                raise("Connection to redis server was not established")

        except Exception as e:
            self.logger.error("Problem during connecting to Redis server!")
            print(e)

    def insert_values_dict(self, values_dict):

        try:
            for key in values_dict:
                self.client.hset(key, mapping=values_dict[key])

        except Exception as e:
            self.logger.error("Problem during inserting list of key-values dictionaries into Redis database!")
            self.client.close()
            print(e)

    def flush_database(self):

        try:
            self.client.flushall()

        except Exception as e:
            self.logger.error("Problem during flushing Redis database")
            self.client.close()
            print(e)

    def filter_keys(self, subkey = None, subvalue = None):

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
            data_embeddings = np.array([eval(self.client.hmget(key, ['embedding'])[0]) for key in self.keys_list])

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

        results = [dict(zip(return_keys_list, self.client.hmget(searched_doc, return_keys_list))) \
            for searched_doc in self.results_keys]

        return results

