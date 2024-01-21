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
import numpy as np #==1.26.0
import dill #==0.3.7
import attr #>=22.2.0
## for making keys
import hashlib
## for search
import hnswlib #0.7.0
from sentence_transformers import SentenceTransformer #==2.2.2


# Metadata for package creation
__package_metadata__ = {
    "author": "Kyrylo Mordan",
    "author_email": "parachute.repo@gmail.com",
    "version": "0.0.1",
    "description": "A mock handler for simulating a vector database.",
    # Add other metadata as needed
}

@attr.s
class SentenceTransformerEmbedder:

    kwargs = attr.ib(factory=dict)

    model = attr.ib(default=None, init=False)

    logger = attr.ib(default=None)
    logger_name = attr.ib(default='Mock handler')
    loggerLvl = attr.ib(default=logging.INFO)
    logger_format = attr.ib(default=None)


    def __init__(self, **kwargs):
        self.__attrs_init__()
        self._initialize_logger()
        # Suppress SentenceTransformer logging
        logging.getLogger('sentence_transformers').setLevel(logging.ERROR)
        self.model = SentenceTransformer(**kwargs)


    def __attrs_post_init__(self):
        self._initialize_logger()
        # Suppress SentenceTransformer logging
        logging.getLogger('sentence_transformers').setLevel(logging.ERROR)
        self.model = SentenceTransformer(**self.kwargs)

    def _initialize_logger(self):

        """
        Initialize a logger for the class instance based on the specified logging level and logger name.
        """

        if self.logger is None:
            logging.basicConfig(level=self.loggerLvl, format=self.logger_format)
            logger = logging.getLogger(self.logger_name)
            logger.setLevel(self.loggerLvl)

            self.logger = logger

    def embed_sentence_transformer(self, text):

        """
        Embeds single query with sentence tranformer embedder.
        """

        return self.model.encode(text)

    def embed(self, text):

        """
        Embeds single query with sentence with selected embedder.
        """

        return self.embed_sentence_transformer(text = text)


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

    """

    ## for accessing openAI models
    embeddings_url = attr.ib(default=None)
    godID = attr.ib(default=None)
    headers = attr.ib(default=None)

    ## for embeddings
    embedder_params = attr.ib(default={'model_name_or_path' : 'paraphrase-multilingual-mpnet-base-v2'})
    embedder = attr.ib(default=SentenceTransformerEmbedder)


    ## for similarity search
    return_keys_list = attr.ib(default=[], type = list)
    search_results_n = attr.ib(default=3, type = int)
    similarity_search_type = attr.ib(default='linear', type = str)
    similarity_params = attr.ib(default={'space':'cosine'}, type = dict)

    ## inputs with defaults
    file_path = attr.ib(default="./redis_mock", type=str)
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
    results_dictances = attr.ib(default=None, init = False)

    def __attrs_post_init__(self):
        self._initialize_logger()
        self.embedder = self.embedder(kwargs = self.embedder_params,
                                      logger = self.logger)

    def _initialize_logger(self):

        """
        Initialize a logger for the class instance based on the specified logging level and logger name.
        """

        if self.logger is None:
            logging.basicConfig(level=self.loggerLvl, format=self.logger_format)
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

    def linear_search(self, search_emb, doc_embs, k=1, space='cosine'):

        """
        Perform a linear (brute force) search.

        Args:
        - search_emb (numpy array): The query embedding. Shape (1, dim).
        - doc_embs (numpy array): Array of reference embeddings. Shape (num_elements, dim).
        - k (int): Number of nearest neighbors to return.
        - space (str): Space type for the distance calculation ('cosine' or 'l2').

        Returns:
        - labels (numpy array): Indices of the k nearest embeddings from doc_embs to search_emb.
        - distances (numpy array): Distances of the k nearest embeddings.
        """

        # Calculate distances from the query to all document embeddings
        if space == 'cosine':
            # Normalize embeddings for cosine similarity
            search_emb_norm = search_emb / np.linalg.norm(search_emb)
            doc_embs_norm = doc_embs / np.linalg.norm(doc_embs, axis=1)[:, np.newaxis]

            # Compute cosine distances
            distances = np.dot(doc_embs_norm, search_emb_norm.T).flatten()
        elif space == 'l2':
            # Compute L2 distances
            distances = np.linalg.norm(doc_embs - search_emb, axis=1)

        # Get the indices of the top k closest embeddings
        if space == 'cosine':
            # For cosine, larger values mean closer distance
            labels = np.argsort(-distances)[:k]
        else:
            # For L2, smaller values mean closer distance
            labels = np.argsort(distances)[:k]

        # Get the distances of the top k closest embeddings
        top_distances = distances[labels]

        return labels, top_distances

    def establish_connection(self, file_path : str = None):

        """
        Simulates establishing a connection by loading data from a local file into the 'data' attribute.
        """

        if file_path is None:
            file_path = self.file_path

        try:
            with open(file_path, 'rb') as file:
                self.data = dill.load(file)
        except FileNotFoundError:
            self.data = {}
        except Exception as e:
            self.logger.error("Error loading data from file: ", e)

    def save_data(self):

        """
        Saves the current state of 'data' back into a local file.
        """

        if self.persist:
            try:
                with open(self.file_path, 'wb') as file:
                    dill.dump(self.data, file)
            except Exception as e:
                self.logger.error("Error saving data to file: ", e)

    def hash_string_sha256(self,input_string):
        return hashlib.sha256(input_string.encode()).hexdigest()

    def _make_key(self,input_string):
        return self.hash_string_sha256(input_string)

    def _prepare_for_insert(self, data_dict, var_for_embedding_name):

        """
        Prepare a dictionary for storage in Redis by serializing all its values to strings.
        """


        for key, _ in data_dict.items():

            embedding = self.embedder.embed(str(data_dict[key][var_for_embedding_name]))
            data_dict[key]['embedding'] = embedding


        return data_dict

    def _insert_values_dict_i(self, values_dict, var_for_embedding_name, embed = True):

        """
        Simulates inserting key-value pair into the mock database.
        """

        try:
            if embed:
                values_dict = self._prepare_for_insert(data_dict = values_dict,
                                                    var_for_embedding_name = var_for_embedding_name)
            self.data.update(values_dict)

            return 0

        except Exception as e:
            return 1
            self.logger.error("Problem during inserting list of key-values dictionaries into mock database!", e)

    def insert_values_dict(self, values_dict, var_for_embedding_name, embed : bool = True):

        """
        Simulates inserting key-value pairs into the mock Redis database.
        """

        try:


            error_list = [self._insert_values_dict_i(values_dict = insd,
                                        var_for_embedding_name = var_for_embedding_name,
                                        embed = embed) for insd in values_dict]
            errors = sum(error_list)
            if errors == 0:
                self.save_data()
            else:

                raise ValueError(f"Errors in ({[index for index, value in enumerate(error_list) if value == 1]}) during updating insertion: {errors}")

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

    def filter_database(self, filter_criteria : dict = None):

        """
        Filters a dictionary based on multiple field criteria.
        """

        self.filtered_data = {
            key: value for key, value in self.data.items()
            if all(value.get(k) == v for k, v in filter_criteria.items())
        }

    def remove_from_database(self, filter_criteria : dict = None):
        """
        Removes key-value pairs from a dictionary based on filter criteria.
        """

        self.data = {
            key: value for key, value in self.data.items()
            if not all(value.get(k) == v for k, v in filter_criteria.items())
        }

    def search_database_keys(self,
        query: str,
        search_results_n: int = None,
        similarity_search_type: str = None,
        similarity_params: dict = None,
        perform_similarity_search: bool = None):

        """
        Searches the mock database using embeddings and saves a list of entries that match the query.
        """

        try:
            query_embedding = self.embedder.embed(query)
        except Exception as e:
            self.logger.error("Problem during embedding search query!", e)


        if search_results_n is None:
            search_results_n = self.search_results_n

        if similarity_search_type is None:
            similarity_search_type = self.similarity_search_type

        if similarity_params is None:
            similarity_params = self.similarity_params

        if self.filtered_data is None:
            self.filtered_data = self.data

        if self.keys_list is None:
            self.keys_list = [key for key in self.filtered_data]

        if perform_similarity_search is None:
            perform_similarity_search = True

        if perform_similarity_search:

            try:
                data_embeddings = np.array([(self.filtered_data[d]['embedding']) for d in self.keys_list])
            except Exception as e:
                self.logger.error("Problem during extracting search pool embeddings!", e)

            try:
                if similarity_search_type == 'linear':
                    labels, distances = self.linear_search(query_embedding,
                    data_embeddings,
                    k=search_results_n,
                    **similarity_params)
                else:
                    labels, distances = self.hnsw_search(query_embedding,
                    data_embeddings,
                    k=search_results_n,
                    **similarity_params)

                self.results_keys = [self.keys_list[i] for i in labels]
                self.results_dictances = distances

            except Exception as e:
                self.logger.error("Problem during extracting results from the mock database!", e)


        else:

            try:
                self.results_keys = [result_key for result_key in self.filtered_data]
                self.results_dictances = np.array([0 for result_key in self.filtered_data])
            except Exception as e:
                self.logger.error("Problem during extracting search pool embeddings!", e)




    def get_dict_results(self, return_keys_list : list = None) -> list:

        """
        Retrieves specified fields from the search results in the mock database.
        """

        if return_keys_list is None:
            return_keys_list = self.return_keys_list

        # This method mimics the behavior of the original 'get_dict_results' method
        results = []
        for searched_doc in self.results_keys:
            result = {key: self.data[searched_doc].get(key) for key in return_keys_list}
            results.append(result)
        return results

    def search_database(self,
        query: str,
        search_results_n: int = None,
        filter_criteria : dict = None,
        similarity_search_type: str = None,
        similarity_params: dict = None,
        perform_similarity_search: bool = None,
        return_keys_list : list = None) ->list:

        """
        Searches through keys and retrieves specified fields from the search results
        in the mock database for a given filter.
        """

        if filter_criteria:
            self.filter_database(filter_criteria=filter_criteria)

        self.search_database_keys(query = query,
                                    search_results_n = search_results_n,
                                    similarity_search_type = similarity_search_type,
                                    similarity_params = similarity_params,
                                    perform_similarity_search = perform_similarity_search)

        results = self.get_dict_results(return_keys_list = return_keys_list)

        # resetting search
        self.filtered_data = None
        self.keys_list = None

        return results