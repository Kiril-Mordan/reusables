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
import numpy as np
import dill
import attr
## for search
import requests
import hnswlib



@attr.s
class MockVecDbHandler:
    # pylint: disable=too-many-instance-attributes

    """
    This class is a mock handler for simulating a vector database, designed primarily for testing and development scenarios.
    It offers functionalities such as text embedding, hierarchical navigable small world (HNSW) search,
    and basic data management within a simulated environment resembling a vector database.

    Parameters:
    - embeddings_url (str): The URL to access OpenAI models for generating embeddings, essential for text analysis and comparison.
    - godID (str): A unique identifier used for authentication when interacting with the embedding service, ensuring secure access.
    - headers (dict): HTTP headers required for making requests to the embedding service, crucial for successful API interactions.
    - file_path (str, optional): The local file path used for storing and simulating the database, with a default value for quick setup.
    - logger (logging.Logger, optional): An optional logger instance to log activities and events within the class,
    aiding in debugging and monitoring.
    - logger_name (str, optional): The designated name for the logger, allowing for easy identification in logs.
    - loggerLvl (int, optional): The logging level, determining the verbosity of log messages, set to INFO by default for balanced logging.

    Instance Variables:
    - data (dict): A simulated in-memory representation of the database contents, used for testing data retrieval and storage operations.
    - keys_list (list): A dynamically generated list of keys present in the simulated database, useful for search and retrieval operations.
    - results_keys (list): A list of keys that match specific search criteria, updated after each search operation.

    Key Methods:
    - initialize_logger(): Sets up a logging mechanism for the class, enhancing traceability and debugging.
    - hnsw_search(): Implements the HNSW algorithm to efficiently search in high-dimensional spaces,
    crucial for vector database operations.
    - establish_connection(): Simulates the process of establishing a connection to a database by loading data from a file.
    - save_data(): Persists the current state of the 'data' attribute to a file, mimicking the data persistence in a database.
    - embed(): Generates embeddings for given text inputs using an external API, a fundamental operation for text-based vector databases.

    The class also includes additional methods for simulating database insertions, updates, filtering, and searching, providing a
    comprehensive tool for testing vector database interactions in a controlled environment.
    """

    ## for accessing openAI models
    embeddings_url = attr.ib()
    godID = attr.ib()
    headers = attr.ib()

    ## inputs with defaults
    file_path = attr.ib(default="../redis_mock", type=str)

    logger = attr.ib(default=None)
    logger_name = attr.ib(default='Mock handler')
    loggerLvl = attr.ib(default=logging.INFO)

    ## outputs
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


    def hnsw_search(self, search_emb, doc_embs, k=1, space='cosine', ef_search=50, M=16, ef_construction=200):
        """
        Perform Hierarchical Navigable Small World search.

        Args:
        - search_emb (numpy array): The query embedding. Shape (1, dim).
        - doc_embs (numpy array): Array of reference embeddings. Shape (num_elements, dim).
        - k (int): Number of nearest neighbors to return.
        - space (str): Space type for the index ('cosine' or 'l2').
        - ef_search (int): Search parameter. Higher means more accurate but slower.
        - M (int): Index parameter.
        - ef_construction (int): Index construction parameter.

        Returns:
        - labels (numpy array): Indices of the k nearest embeddings from doc_embs to search_emb.
        - distances (numpy array): Distances of the k nearest embeddings.
        """

        # Declare index
        dim = len(search_emb)#.shape[1]
        p = hnswlib.Index(space=space, dim=dim)

        # Initialize the index using the data
        p.init_index(max_elements=len(doc_embs), ef_construction=ef_construction, M=M)

        # Add data to index
        p.add_items(doc_embs)

        # Set the query ef parameter
        p.set_ef(ef_search)

        # Query the index
        labels, distances = p.knn_query(search_emb, k=k)

        return labels[0], distances[0]

    def establish_connection(self):

        """
        Simulates establishing a connection by loading data from a local file into the 'data' attribute.
        """

        try:
            with open(self.file_path, 'rb') as file:
                self.data = dill.load(file)
        except FileNotFoundError:
            self.data = {}
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

    def embed(self, text):

        """
        Embeds single query with openAI embedder.
        """

        api_url = self.embeddings_url

        payload = json.dumps({
            "user": self.godID,
            "input": text
        })

        try:
            response = requests.post(api_url, headers=self.headers, data=payload, timeout=10)

            if response.status_code == 429:
                time.sleep(1)
                response = requests.post(api_url, headers=self.headers, data=payload, timeout=10)

            if response.status_code > 200:
                print(f"Request to '{api_url}' failed: {response}")
                print(response.text)
                return None

            embedding = response.json()['data'][0]['embedding']

        except:
            print("An exception has occurred during embedding!")
            return None
        # with open('embeddings_backup.p' , 'rb')  as f:
        #     embeddings = pickle.load(f)
        return embedding

    def _prepare_for_redis(self, data_dict, var_for_embedding_name):

        """
        Prepare a dictionary for storage in Redis by serializing all its values to strings.
        """

        for key, _ in data_dict.items():

            embedding = self.embed(data_dict[key][var_for_embedding_name])
            data_dict[key]['embedding'] = embedding

        return data_dict


    def insert_values_dict(self, values_dict, var_for_embedding_name):

        """
        Simulates inserting key-value pairs into the mock Redis database.
        """

        try:

            values_dict = self._prepare_for_redis(data_dict = values_dict,
                                                  var_for_embedding_name = var_for_embedding_name)

            self.data.update(values_dict)
            self.save_data()
        except Exception as e:
            self.logger.error("Problem during inserting list of key-values dictionaries into mock database!", e)

    def flush_database(self):

        """
        Clears all data in the mock database.
        """

        try:
            self.data = {}
            self.save_data()
        except Exception as e:
            self.logger.error("Problem during flushing mock database", e)

    def filter_keys(self, subkey=None, subvalue=None):

        """
        Filters data entries based on a specific subkey and subvalue.
        """

        if (subkey is not None) and (subvalue is not None):
            self.keys_list = [d for d in self.data if self.data[d][subkey] == subvalue]
        else:
            self.keys_list = self.data

    def search_database_keys(self, query: str, search_results_n: int = 3):

        """
        Searches the mock database using embeddings and returns a list of entries that match the query.
        """

        try:
            query_embedding = self.embed(query)
        except Exception as e:
            self.logger.error("Problem during embedding search query!", e)

        if self.keys_list is None:
            self.keys_list = [key for key in self.data]

        try:
            data_embeddings = np.array([(self.data[d]['embedding']) for d in self.keys_list])
        except Exception as e:
            self.logger.error("Problem during extracting search pool embeddings!", e)

        # self.logger.info(self.keys_list)
        # self.logger.info(data_embeddings)

        try:
            labels, _ = self.hnsw_search(query_embedding, data_embeddings, k=search_results_n)
            self.results_keys = [self.keys_list[i] for i in labels]
        except Exception as e:
            self.logger.error("Problem during extracting results from the mock database!", e)

    def get_dict_results(self, return_keys_list) -> dict:

        """
        Retrieves specified fields from the search results in the mock database.
        """

        # This method mimics the behavior of the original 'get_dict_results' method
        results = {}
        for searched_doc in self.results_keys:
            result = {key: self.data[searched_doc].get(key) for key in return_keys_list}
            results.update(result)
        return results
