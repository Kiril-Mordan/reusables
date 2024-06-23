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
import copy
import numpy as np #==1.26.0
import dill #==0.3.7
import attr #>=22.2.0
## for making keys
import hashlib
## for search
import concurrent.futures
import hnswlib #==0.8.0
from sentence_transformers import SentenceTransformer #==2.2.2


# Metadata for package creation
__package_metadata__ = {
    "author": "Kyrylo Mordan",
    "author_email": "parachute.repo@gmail.com",
    "version": "0.0.1",
    "description": "A mock handler for simulating a vector database.",
    # Add other metadata as needed
}


class SentenceTransformerEmbedder:

    def __init__(self,tbatch_size = 32, processing_type = 'batch', max_workers = 2, *args, **kwargs):
        # Suppress SentenceTransformer logging
        logging.getLogger('sentence_transformers').setLevel(logging.ERROR)
        self.tbatch_size = tbatch_size
        self.processing_type = processing_type
        self.max_workers = max_workers
        self.model = SentenceTransformer(*args, **kwargs)

    def embed_sentence_transformer(self, text):

        """
        Embeds single query with sentence tranformer embedder.
        """

        return self.model.encode(text)

    def embed(self, text, processing_type : str = None):

        """
        Embeds single query with sentence with selected embedder.
        """

        if processing_type is None:
            processing_type = self.processing_type

        if processing_type == 'batch':
           return self.embed_texts_in_batches(texts = text)

        if processing_type == 'parallel':
           return self.embed_sentences_in_batches_parallel(texts = text)

        return self.embed_sentence_transformer(text = str(text))

    def embed_texts_in_batches(self, texts, batch_size : int = None):
        """
        Embeds a list of texts in batches.
        """
        if batch_size is None:
            batch_size = self.tbatch_size

        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = self.model.encode(batch, show_progress_bar=False)
            embeddings.extend(batch_embeddings)
        return embeddings

    def embed_sentences_in_batches_parallel(self, texts, batch_size : int = None, max_workers : int =  None):

        """
        Embeds a list of texts in batches in parallel.
        """

        if batch_size is None:
            batch_size = self.tbatch_size

        if max_workers is None:
            max_workers = self.max_workers


        # Split texts into batches
        batches = [texts[i:i + batch_size] for i in range(0, len(texts), batch_size)]

        # Process batches in parallel
        embeddings = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit embedding tasks to the executor
            future_to_batch = {executor.submit(self.embed_sentence_transformer, batch): batch for batch in batches}

            for future in concurrent.futures.as_completed(future_to_batch):
                embeddings.extend(future.result())

        return embeddings

@attr.s
class MockerSimilaritySearch:


    search_results_n = attr.ib(default=3, type=int)
    similarity_params = attr.ib(default={'space':'cosine'}, type=dict)
    similarity_search_type = attr.ib(default='linear')

    # output
    hnsw_index = attr.ib(init=False)

    logger = attr.ib(default=None)
    logger_name = attr.ib(default='Similarity search')
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

        self.hnsw_index = p

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

    def search(self,
               query_embedding,
               data_embeddings,
               k : int = None,
               similarity_search_type: str = None,
               similarity_params : dict = None):


        if k is None:
            k = self.search_results_n
        if similarity_search_type is None:
            similarity_search_type = self.similarity_search_type
        if similarity_params is None:
            similarity_params = self.similarity_params

        if similarity_search_type == 'linear':
            return self.linear_search(search_emb = query_embedding, doc_embs = data_embeddings, k=k, **similarity_params)
        if similarity_search_type == 'hnsw':
            return self.hnsw_search(search_emb = query_embedding, doc_embs = data_embeddings, k=k, **similarity_params)



@attr.s
class MockerDB:
    # pylint: disable=too-many-instance-attributes

    """
    The MockerDB class simulates a vector database environment, primarily for testing and development purposes.
    It integrates various functionalities such as text embedding, Hierarchical Navigable Small World (HNSW) search,
    and basic data management, mimicking operations in a real vector database.

    Parameters:
        file_path (str): Local file path for storing and simulating the database; defaults to "../mock_persist".
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

    ## for embeddings
    embedder_params = attr.ib(default={'model_name_or_path' : 'paraphrase-multilingual-mpnet-base-v2',
                                       'processing_type' : 'batch',
                                       'tbatch_size' : 500})
    embedder = attr.ib(default=SentenceTransformerEmbedder)


    ## for similarity search
    similarity_search_h = attr.ib(default=MockerSimilaritySearch)
    return_keys_list = attr.ib(default=[], type = list)
    search_results_n = attr.ib(default=3, type = int)
    similarity_search_type = attr.ib(default='linear', type = str)
    similarity_params = attr.ib(default={'space':'cosine'}, type = dict)

    ## inputs with defaults
    file_path = attr.ib(default="./mock_persist", type=str)
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
        self.embedder = self.embedder(**self.embedder_params)
        self.similarity_search_h = self.similarity_search_h(similarity_search_type = self.similarity_search_type,
                                                            search_results_n = self.search_results_n,
                                                            similarity_params = self.similarity_params,
                                                            logger = self.logger)
        self.data = {}

    def _initialize_logger(self):

        """
        Initialize a logger for the class instance based on the specified logging level and logger name.
        """

        if self.logger is None:
            logging.basicConfig(level=self.loggerLvl, format=self.logger_format)
            logger = logging.getLogger(self.logger_name)
            logger.setLevel(self.loggerLvl)

            self.logger = logger



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

    def _make_key(self,d, embed):

        input_string = json.dumps(d) + str(embed)

        return self.hash_string_sha256(input_string)

    def _add_embeddings(self, data_dict, var_for_embedding_name):

        """
        Prepare a dictionary for storage in Mocker by adding embedding.
        """

        try:

            embedding = self.embedder.embed(data_dict[var_for_embedding_name])
            data_dict['embedding'] = embedding

        except Exception as e:
            return 1

        return data_dict



    def _insert_values_dict(self, values_dicts, var_for_embedding_name, embed = True):

        """
        Simulates inserting key-value pair into the mock database.
        """


        if embed:

            list_of_text_to_embed = [values_dicts[insd][var_for_embedding_name] for insd in values_dicts]

            if self.embedder.processing_type in ['parallel', 'batch']:

                embedded_list_of_text = self.embedder.embed(text = list_of_text_to_embed)

            else:

                embedded_list_of_text = [self.embedder.embed(text = text_to_embed) for text_to_embed in list_of_text_to_embed]

            i = 0
            for insd in values_dicts:
                values_dicts[insd]['embedding'] = embedded_list_of_text[i]
                i = i + 1

        self.data.update(values_dicts)
        self.save_data()


    def insert_values(self, values_dict_list, var_for_embedding_name, embed : bool = True):

        """
        Simulates inserting key-value pairs into the mock Redis database.
        """

        values_dict_list = copy.deepcopy(values_dict_list)

        try:
            # make unique keys, taking embed parameter as a part of a key
            values_dict_all = {self._make_key(d = d, embed=embed) : d for d in values_dict_list}
        except Exception as e:
            self.logger.error("Problem during making unique keys foir insert dicts!", e)

        try:
            # check if keys exist in data
            values_dict_filtered = {key : values_dict_all[key] for key in values_dict_all.keys() if key not in self.data.keys()}

        except Exception as e:
            self.logger.error("Problem during filtering out existing inserts!", e)

        if values_dict_filtered != {}:
            try:
                # insert new values
                self._insert_values_dict(values_dicts = values_dict_filtered,
                                                    var_for_embedding_name = var_for_embedding_name,
                                                    embed = embed)

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
            query_embedding = self.embedder.embed(query, processing_type='single')
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

                labels, distances = self.similarity_search_h.search(query_embedding = query_embedding,
                                                                    data_embeddings = data_embeddings,
                                                                    k=search_results_n,
                                                                    similarity_search_type = similarity_search_type,
                                                                    similarity_params = similarity_params)


                self.results_keys = [self.keys_list[i] for i in labels]
                self.results_dictances = distances

            except Exception as e:
                self.logger.error("Problem during extracting results from the mock database!", e)


        else:

            try:
                self.results_keys = [result_key for result_key in self.filtered_data]
                self.results_dictances = np.array([0 for _ in self.filtered_data])
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