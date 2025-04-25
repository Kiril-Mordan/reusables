"""
`mocker-db` is a python module that contains mock vector database like solution built around
python dictionary data type. It contains methods necessary to interact with this 'database',
embed, search and persist.
"""

# Imports
## essential
import logging
import json
import time
import copy
import hashlib
from difflib import get_close_matches

import nest_asyncio
import asyncio

import numpy as np  #==1.26.0
import dill  #>=0.3.7
import attrsx
import attrs  #>=23.1.0

from gridlooper import GridLooper  #>=0.0.1

# local dependencies
from .components.mocker_db_deps.sentence_transformer_embedder import SentenceTransformerEmbedder
from .components.mocker_db_deps.mocker_similarity_search import MockerSimilaritySearch
from .components.mocker_db_deps.mocker_connector import MockerConnector
from .components.mocker_db_deps.llm_filter_connector import LlmFilterConnector
from .components.mocker_db_deps.llm_handler import LlmHandler, BaseLlmHandler

# dependencies for routes
from .components.mocker_db_deps.data_types import InitializeParams, InsertItem, SearchRequest, DeleteItem, UpdateItem, EmbeddingRequest, RemoveHandlersRequest
from .components.mocker_db_deps.memory_management import check_and_offload_handlers, obj_size
from .components.mocker_db_deps.other import extract_directory
from .components.mocker_db_deps.response_descriptions import ActivateHandlersDesc, RemoveHandlersDesc, InitializeDesc, InsertDesc, SearchDesc, DeleteDesc, EmbedDesc



# Metadata for package creation
__package_metadata__ = {
    "author": "Kyrylo Mordan",
    "author_email": "parachute.repo@gmail.com",
    "description": "A mock handler for simulating a vector database.",
    "license": "mit",
    "url": "https://kiril-mordan.github.io/reusables/mocker_db/",
}


@attrsx.define
class MockerDB:

    """
    The MockerDB class simulates a vector database environment, primarily for testing and development purposes.
    It integrates various functionalities such as text embedding, Hierarchical Navigable Small World (HNSW) search,
    and basic data management, mimicking operations in a real vector database.

    Parameters:
        file_path (str): Local file path for storing and simulating the database; defaults to "../mock_persist".
        persist (bool): Flag to persist data changes; defaults to False.
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
    embedder_params = attrs.field(
        default={
            "model_name_or_path": "paraphrase-multilingual-mpnet-base-v2",
            "processing_type": "batch",
            "tbatch_size": 500,
        }
    )
    use_embedder = attrs.field(default=True)
    embedder = attrs.field(default=SentenceTransformerEmbedder)

    ## for llm filter
    llm_filter_params = attrs.field(default={})
    llm_filter = attrs.field(default=LlmFilterConnector)

    llm_conn = attrs.field(default=LlmHandler)
    llm_conn_params = attrs.field(default={})

    ignore_cats_cache = attrs.field(default=False)

    ## for similarity search
    similarity_params = attrs.field(default={"space": "cosine"}, type=dict)
    similarity_search = attrs.field(default=MockerSimilaritySearch)

    ## for conneting to remote mocker
    mdbc_h_params = attrs.field(default={})
    mdbc_class = attrs.field(default=MockerConnector)

    ## activate dependencies
    llm_conn_h = attrs.field(default=None)
    llm_filter_h = attrs.field(default=None)
    embedder_h = attrs.field(default=None)
    similarity_search_h = attrs.field(default=None)
    mdbc_h = attrs.field(default=None)

    ##
    return_keys_list = attrs.field(default=None, type=list)
    ignore_keys_list = attrs.field(
        default=["embedding", "&distance", "&id", "&embedded_field", "&cats"], type=list
    )
    search_results_n = attrs.field(default=10000, type=int)
    similarity_search_type = attrs.field(default="linear", type=str)
    keyword_check_cutoff = attrs.field(default=1, type=float)

    ## inputs with defaults
    file_path = attrs.field(default="./mock_persist", type=str)
    embs_file_path = attrs.field(default="./mock_embs_persist", type=str)
    cats_file_path = attrs.field(default="./mock_cats_persist", type=str)
    persist = attrs.field(default=False, type=bool)

    skip_post_init = attrs.field(default=False)

    ## data
    data = attrs.field(default=None, init=False)
    embs = attrs.field(default=None, init=False)
    cats = attrs.field(default=None, init=False)

    ## outputs
    filtered_data = attrs.field(default=None, init=False)
    keys_list = attrs.field(default=None, init=False)
    results_keys = attrs.field(default=None, init=False)
    results_dictances = attrs.field(default=None, init=False)

    def __attrs_post_init__(self):
        if not self.skip_post_init:
            self._initialize_llm_connection()
            self._initialize_llm_filter()
            self._initialize_embedder()
            self._initialize_sim_search()

        self.data = {}

    def _initialize_llm_connection(self):
        """
        Initializes llm connection with provided parameters.
        """

        if (self.llm_conn_h is None) and (self.llm_conn_params != {}):
            self.llm_conn_h = self.llm_conn(
                **self.llm_conn_params, 
                logger=self.logger
            )

    def _initialize_llm_filter(self):
        """
        Initializes llm filter with provided parameters.
        """

        if (self.llm_filter_h is None) and (self.llm_conn_h is not None):
            self.llm_filter_h = self.llm_filter(
                **self.llm_filter_params, 
                llm_h = self.llm_conn_h,
                logger=self.logger
            )

    def _initialize_embedder(self):
        """
        Initializes embedder connector with provided parameters.
        """
        if self.use_embedder:

            if self.embedder_h is None:
                self.embedder_h = self.embedder(**self.embedder_params)

    def _initialize_sim_search(self):
        """
        Initializes embedder connector with provided parameters.
        """

        if self.similarity_search_h is None:
            self.similarity_search_h = self.similarity_search(
                similarity_search_type=self.similarity_search_type,
                search_results_n=self.search_results_n,
                similarity_params=self.similarity_params,
                logger=self.logger,
            )

    def _hash_string_sha256(self, input_string: str) -> str:
        return hashlib.sha256(input_string.encode()).hexdigest()

    def _make_key(self, d: dict, embed: bool) -> str:

        input_string = json.dumps(d) + str(embed)

        return self._hash_string_sha256(input_string)

    def _make_embs_key(self, text: str, model: str) -> str:

        input_string = str(text) + str(model)

        return self._hash_string_sha256(input_string)

    def _prep_filter_criterias(self, filter_criteria: dict) -> list:
        """
        Makes a list of filters based on provided filter.
        """

        filter_criteria = {
            key: value if isinstance(value, list) else [value]
            for key, value in filter_criteria.items()
        }

        gl = GridLooper()
        gl.prepare_search_grid(experiments_settings=filter_criteria)

        filter_criterias = gl.experiment_configs

        filter_criterias = [
            {k: v for k, v in filter_dict.items() if k != "config_id"}
            for filter_dict in filter_criterias
        ]

        return filter_criterias

    def _insert_values_dict(
        self,
        values_dicts: dict,
        var_for_embedding_name: str,
        model_name: str = None,
        embed: bool = True,
    ) -> None:
        """
        Simulates inserting key-value pair into the mock database.
        """

        if embed:

            if model_name is None:
                model_name = self.embedder_params["model_name_or_path"]

            list_of_text_to_embed = [
                values_dicts[insd][var_for_embedding_name] for insd in values_dicts
            ]

            # generate list of hashes
            list_of_hash_for_embeddings = [
                self._make_embs_key(text=text, model=model_name)
                for text in list_of_text_to_embed
            ]

            # check which embeddings are not present already
            if model_name not in list(self.embs.keys()):
                self.embs[model_name] = {}

            current_embs_keys = list(self.embs[model_name].keys())
            filtered_list_of_text_to_embed = []
            existing_list_of_embeddings = []

            for new_hash, new_text in zip(
                list_of_hash_for_embeddings, list_of_text_to_embed
            ):
                if new_hash is not current_embs_keys:
                    filtered_list_of_text_to_embed.append(new_text)
                else:
                    existing_list_of_embeddings.append(self.embs[model_name][new_hash])

            # embed new with embedder
            if self.embedder_h.processing_type in ["parallel", "batch"]:
                new_embedded_list_of_text = self.embedder_h.embed(
                    text=filtered_list_of_text_to_embed
                )
            else:
                new_embedded_list_of_text = [
                    self.embedder_h.embed(text=text_to_embed)
                    for text_to_embed in filtered_list_of_text_to_embed
                ]

            embedded_list_of_text = []
            # construct embeddings list from new and stored
            for new_hash, new_text in zip(
                list_of_hash_for_embeddings, list_of_text_to_embed
            ):
                if new_hash is not current_embs_keys:
                    new_embedding = new_embedded_list_of_text.pop(0)
                    embedded_list_of_text.append(new_embedding)
                    # update embeddigs in embeddings storage
                    self.embs[model_name][new_hash] = new_embedding
                else:
                    embedded_list_of_text.append(existing_list_of_embeddings.pop(0))

            # adding embeddings to data
            i = 0
            for insd in values_dicts:
                values_dicts[insd]["&embedded_field"] = var_for_embedding_name
                values_dicts[insd]["embedding"] = embedded_list_of_text[i]
                i = i + 1

        # update data with embeddings
        self.data.update(values_dicts)
        # apply persist strategy
        self.save_data()

    def _check_if_match(self, content: str, cutoff: float, keyword_set: list):
        words = set(content.split())
        match = any(
            get_close_matches(keyword, words, cutoff=cutoff) for keyword in keyword_set
        )
        return match

    def _get_close_matches_for_keywords(
        self, data_key: str, keywords: list, cutoff: float
    ):
        # Preprocess keywords into a set for faster membership checking
        keyword_set = set(keywords)
        matched_keys = set()

        if cutoff < 1:

            keyword_set = [keyword.lower() for keyword in keyword_set]

            matched_data = {
                key: value
                for key, value in self.data.items()
                if self._check_if_match(
                    content=value[data_key].lower(),
                    cutoff=cutoff,
                    keyword_set=keyword_set,
                )
            }
        else:
            matched_data = {
                key: value
                for key, value in self.data.items()
                if self._check_if_match(
                    content=value[data_key], cutoff=cutoff, keyword_set=keyword_set
                )
            }

        return matched_data

    def _filter_database(
        self,
        filter_criteria: dict = None,
        llm_search_keys: list = None,
        keyword_check_keys: list = None,
        keyword_check_cutoff: float = None,
    ):
        """
        Filters a dictionary based on multiple field criteria.
        """

        if keyword_check_cutoff is None:
            keyword_check_cutoff = self.keyword_check_cutoff

        if keyword_check_keys is None:
            keyword_check_keys = []

        if llm_search_keys is None:
            llm_search_keys = []

        keyword_check_dict = {}
        llm_search_check_dict = {}

        filter_criteria_list = []
        if filter_criteria:
            for key in keyword_check_keys:
                keyword_check_dict[key] = filter_criteria[key]
                del filter_criteria[key]

            for key in llm_search_keys:
                llm_search_check_dict[key] = filter_criteria[key]
                del filter_criteria[key]

            if filter_criteria:
                filter_criteria_list = self._prep_filter_criterias(
                    filter_criteria=filter_criteria
                )

        self.filtered_data = {}

        if keyword_check_keys:

            filtered_data = {}

            for key, keywords in keyword_check_dict.items():
                filtered_data = self._get_close_matches_for_keywords(
                    data_key=key, keywords=keywords, cutoff=keyword_check_cutoff
                )
                self.filtered_data.update(filtered_data)

        if filter_criteria_list:

            filtered_data = {}

            filtered_data = {
                key: value
                for key, value in self.data.items()
                if any(
                    all(value.get(k) == v for k, v in filter_dict.items())
                    for filter_dict in filter_criteria_list
                )
            }

            self.filtered_data.update(filtered_data)

        return {
            "llm_search_keys": llm_search_keys,
            "keyword_check_keys": keyword_check_keys,
            "filter_criteria_list": filter_criteria_list,
            "llm_search_check_dict": llm_search_check_dict,
        }

    def _update_cats_cache(self, cache_update : dict):

        for text, cats in cache_update.items():


            if text not in self.cats.keys():
                self.cats[text] = {1 : [], 0 : []}

            self.cats[text][1] = list(set(self.cats[text][1] + cats[1]))
            self.cats[text][0] = list(set(self.cats[text][0] + cats[0]))

    def _update_filtered_cats(self):

        data_update = {dt : {**self.data[dt], "&cats" : di.get("&cats", {})} \
            for dt, di in self.filtered_data.items()}

        self.data.update(data_update)
        self.save_data()

    def _filter_llm(
        self,
        llm_search_keys: bool,
        keyword_check_keys: list,
        filter_criteria_list: list,
        llm_search_check_dict: dict,
        ignore_cats_cache : bool,
    ):

        if llm_search_keys:

            nest_asyncio.apply() 
            loop = asyncio.new_event_loop()

            filtered_data = self.filtered_data
            if keyword_check_keys == [] and filter_criteria_list == []:
                filtered_data = self.data

            cats_cache = self.cats if not ignore_cats_cache else {}

            filtered_data, cats_cache_update = loop.run_until_complete(self.llm_filter_h.filter_data_async(
                data=filtered_data, search_specs = llm_search_check_dict, cats_cache = cats_cache
            ))

            self.filtered_data = filtered_data

            self._update_cats_cache(cache_update = cats_cache_update)

            self._update_filtered_cats()

    async def _filter_llm_async(
        self,
        llm_search_keys: list,
        keyword_check_keys: list,
        filter_criteria_list: list,
        llm_search_check_dict: dict,
        ignore_cats_cache : bool,
    ):

        if llm_search_keys:

            filtered_data = self.filtered_data
            if keyword_check_keys == [] and filter_criteria_list == []:
                filtered_data = self.data

            cats_cache = self.cats if not ignore_cats_cache else {}

            filtered_data, cats_cache_update = await self.llm_filter_h.filter_data_async(
                data=filtered_data, search_specs = llm_search_check_dict, cats_cache = cats_cache
            )

            self.filtered_data = filtered_data

            self._update_cats_cache(cache_update = cats_cache_update)

            self._update_filtered_cats()


    def _search_database_keys(
        self,
        query: str,
        search_results_n: int = None,
        similarity_search_type: str = None,
        similarity_params: dict = None,
        perform_similarity_search: bool = None,
    ):
        """
        Searches the mock database using embeddings and saves a list of entries that match the query.
        """

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
                model_name = self.embedder_params["model_name_or_path"]
                query_hash = self._make_embs_key(text=query, model=model_name)

                if model_name in list(self.embs.keys()):

                    if query_hash not in list(self.embs[model_name].keys()):
                        query_embedding = self.embedder_h.embed(
                            query, processing_type="single"
                        )
                    else:
                        query_embedding = self.embs[model_name][query_hash]
                else:
                    self.embs[model_name] = {}
                    query_embedding = self.embedder_h.embed(
                        query, processing_type="single"
                    )
                    self.embs[model_name][query_hash] = query_embedding

            except Exception as e:
                self.logger.error("Problem during embedding search query!", e)

            try:
                data_embeddings = np.array(
                    [
                        (self.filtered_data[d]["embedding"])
                        for d in self.keys_list
                        if "embedding" in self.filtered_data[d].keys()
                    ]
                )
            except Exception as e:
                self.logger.error(
                    "Problem during extracting search pool embeddings!", e
                )

            try:

                if len(data_embeddings) > 0:
                    labels, distances = self.similarity_search_h.search(
                        query_embedding=query_embedding,
                        data_embeddings=data_embeddings,
                        k=search_results_n,
                        similarity_search_type=similarity_search_type,
                        similarity_params=similarity_params,
                    )

                    self.results_keys = [self.keys_list[i] for i in labels]
                    self.results_dictances = distances
                else:
                    self.results_keys = []
                    self.results_dictances = None

            except Exception as e:
                self.logger.error(
                    "Problem during extracting results from the mock database!", e
                )

        else:

            try:
                self.results_keys = [result_key for result_key in self.filtered_data]
                self.results_dictances = np.array([0 for _ in self.filtered_data])
            except Exception as e:
                self.logger.error(
                    "Problem during extracting search pool embeddings!", e
                )

    def _prepare_return_keys(
        self,
        return_keys_list: list = None,
        remove_list: list = None,
        add_list: list = None,
    ):
        """
        Prepare return keys.
        """

        if return_keys_list is None:
            return_keys_list = self.return_keys_list
        if remove_list is None:
            remove_list = self.ignore_keys_list.copy()
        if add_list is None:
            add_list = []

        return_distance = 0

        if "&distance" in remove_list:
            return_distance = 0
            remove_list.remove("&distance")
        if "&distance" in add_list:
            return_distance = 1
            add_list.remove("&distance")

        if return_keys_list:

            ra_list = [
                s for s in return_keys_list if s.startswith("+") or s.startswith("-")
            ]

            if "embedding" in return_keys_list:
                if "embedding" in remove_list:
                    remove_list.remove("embedding")

            for el in ra_list:

                if el[1:] == "&distance":

                    if el.startswith("+"):
                        return_distance = 1
                    else:
                        return_distance = 0

                else:
                    if el.startswith("+"):
                        if el[1:] not in add_list:
                            add_list.append(el[1:])
                        if el[1:] in remove_list:
                            remove_list.remove(el[1:])
                    else:
                        if el[1:] not in remove_list:
                            remove_list.append(el[1:])
                        if el[1:] in add_list:
                            add_list.remove(el[1:])

                return_keys_list.remove(el)

            if "&distance" in return_keys_list:
                return_keys_list.remove("&distance")
                if return_keys_list:
                    return_distance = 1
                else:
                    return_distance = 2

        return add_list, remove_list, return_keys_list, return_distance

    def _extract_from_data(
        self,
        data: dict,
        distances: list,
        results_keys: list,
        return_keys_list: list,
        add_list: list,
        remove_list: list,
        return_distance: int,
    ):
        """
        Process and filter dictionaries based on specified return and removal lists.
        """

        if return_keys_list:
            remove_set = set(remove_list)
            return_keys_set = set(return_keys_list + add_list) - remove_set
            results = []

            if return_distance >= 1:
                for searched_doc, distance in zip(results_keys, distances):
                    result = {
                        key: data[searched_doc].get(key) for key in return_keys_set
                    }
                    result["&distance"] = distance
                    results.append(result)
            else:
                for searched_doc in results_keys:
                    result = {
                        key: data[searched_doc].get(key) for key in return_keys_set
                    }
                    results.append(result)
        else:
            keys_to_remove_set = set(remove_list)
            results = []

            if return_distance == 1:
                for searched_doc, distance in zip(results_keys, distances):
                    filtered_dict = data[searched_doc].copy()
                    for key in keys_to_remove_set:
                        filtered_dict.pop(key, None)

                    filtered_dict["&distance"] = distance
                    results.append(filtered_dict)
            elif return_distance == 2:
                results = [{"&distance": distance} for distance in distances]

            else:
                for searched_doc in results_keys:
                    filtered_dict = data[searched_doc].copy()
                    for key in keys_to_remove_set:
                        filtered_dict.pop(key, None)
                    results.append(filtered_dict)

        return results

    def _get_dict_results(
        self, return_keys_list: list = None, ignore_keys_list: list = None
    ) -> list:
        """
        Retrieves specified fields from the search results in the mock database.
        """

        (add_list, remove_list, return_keys_list, return_distance) = (
            self._prepare_return_keys(
                return_keys_list=return_keys_list, remove_list=ignore_keys_list
            )
        )

        # This method mimics the behavior of the original 'get_dict_results' method
        return self._extract_from_data(
            data=self.data,
            distances=self.results_dictances,
            results_keys=self.results_keys,
            return_keys_list=return_keys_list,
            add_list=add_list,
            remove_list=remove_list,
            return_distance=return_distance,
        )

    ### EXPOSED METHODS FOR INTERACTION

    def establish_connection(
        self,
        connection_details: dict = None,
        file_path: str = None,
        embs_file_path: str = None,
        cats_file_path: str = None,
    ):
        """
        Simulates establishing a connection by loading data from a local file into the 'data' attribute.
        """

        if connection_details:
            self.mdbc_h = self.mdbc_class(
                connection_details=connection_details, **self.mdbc_h_params
            )

        if file_path is None:
            file_path = self.file_path

        if embs_file_path is None:
            embs_file_path = self.embs_file_path

        if cats_file_path is None:
            cats_file_path = self.cats_file_path

        try:
            with open(file_path, "rb") as file:
                self.data = dill.load(file)
        except FileNotFoundError:
            self.data = {}
        except Exception as e:
            self.logger.error("Error loading data from file: ", e)

        try:
            with open(embs_file_path, "rb") as file:
                self.embs = dill.load(file)
        except FileNotFoundError:
            self.embs = {}
        except Exception as e:
            self.logger.error("Error loading embeddings storage from file: ", e)

        try:
            with open(cats_file_path, "rb") as file:
                self.cats = dill.load(file)
        except FileNotFoundError:
            self.cats = {}
        except Exception as e:
            self.logger.error("Error loading classifiers storage from file: ", e)

    def save_data(self):
        """
        Saves the current state of 'data' back into a local file.
        """

        if self.persist:
            try:
                self.logger.debug("Persisting values")
                with open(self.file_path, "wb") as file:
                    dill.dump(self.data, file)
                with open(self.embs_file_path, "wb") as file:
                    dill.dump(self.embs, file)
                with open(self.cats_file_path, "wb") as file:
                    dill.dump(self.cats, file)
            except Exception as e:
                self.logger.error("Error saving data to file: ", e)

    def insert_values(
        self,
        values_dict_list: list,
        var_for_embedding_name: str = None,
        database_name: str = None,
        embed: bool = True,
    ) -> None:
        """
        Simulates inserting key-value pairs into the mock Redis database.
        """

        if self.mdbc_h:

            mdbc_input = {"data": values_dict_list, "embed": embed}

            if var_for_embedding_name:
                mdbc_input["var_for_embedding_name"] = var_for_embedding_name
            if database_name:
                mdbc_input["database_name"] = database_name

            return self.mdbc_h.insert_data(**mdbc_input)

        values_dict_list = copy.deepcopy(values_dict_list)

        try:
            self.logger.debug("Making unique keys")
            # make unique keys, taking embed parameter as a part of a key
            values_dict_all = {
                self._make_key(d=d, embed=embed): d for d in values_dict_list
            }
            values_dict_all = {
                key: {**values_dict_all[key], "&id": key} for key in values_dict_all
            }
        except Exception as e:
            self.logger.error("Problem during making unique keys foir insert dicts!", e)

        try:
            self.logger.debug("Remove values that already exist")
            # check if keys exist in data
            values_dict_filtered = {
                key: values_dict_all[key]
                for key in values_dict_all.keys()
                if key not in self.data.keys()
            }

        except Exception as e:
            self.logger.error("Problem during filtering out existing inserts!", e)

        if values_dict_filtered != {}:
            try:
                self.logger.debug("Inserting values")
                # insert new values
                self._insert_values_dict(
                    values_dicts=values_dict_filtered,
                    var_for_embedding_name=var_for_embedding_name,
                    embed=embed,
                )

            except Exception as e:
                self.logger.error(
                    "Problem during inserting list of key-values dictionaries into mock database!",
                    e,
                )

    def flush_database(self, handler_names: list = None):
        """
        Clears all data in the mock database.
        """

        if self.mdbc_h:

            if handler_names is None:
                raise ValueError("Missing handler_names input for remote MockerDB!")

            mdbc_input = {"handler_names": handler_names}

            return self.mdbc_h.remove_handlers(**mdbc_input)

        try:
            self.data = {}
            self.save_data()
        except Exception as e:
            self.logger.error("Problem during flushing mock database", e)

    def search_database(
        self,
        query: str = None,
        search_results_n: int = None,
        llm_search_keys: list = None,
        keyword_check_keys: list = None,
        keyword_check_cutoff: float = None,
        filter_criteria: dict = None,
        similarity_search_type: str = None,
        similarity_params: dict = None,
        perform_similarity_search: bool = None,
        ignore_cats_cache : bool = None,
        return_keys_list: list = None,
        database_name: str = None,
    ) -> list:
        """
        Searches through keys and retrieves specified fields from the search results
        in the mock database for a given filter.
        """

        if query is None:
            perform_similarity_search = False

        if ignore_cats_cache is None:
            ignore_cats_cache = self.ignore_cats_cache

        if self.mdbc_h:

            mdbc_input = {}

            if database_name:
                mdbc_input["database_name"] = database_name

            mdbc_input.update(
                {
                    "query": query,
                    "search_results_n": search_results_n,
                    "llm_search_keys": llm_search_keys,
                    "keyword_check_keys": keyword_check_keys,
                    "keyword_check_cutoff": keyword_check_cutoff,
                    "filter_criteria": filter_criteria,
                    "similarity_search_type": similarity_search_type,
                    "similarity_params": similarity_params,
                    "perform_similarity_search": perform_similarity_search,
                    "return_keys_list": return_keys_list,
                    "database_name": database_name,
                }
            )

            return self.mdbc_h.search_data(**mdbc_input)

        if filter_criteria:
            temp = self._filter_database(
                filter_criteria=filter_criteria,
                llm_search_keys=llm_search_keys,
                keyword_check_keys=keyword_check_keys,
                keyword_check_cutoff=keyword_check_cutoff,
            )

            self._filter_llm(**temp, ignore_cats_cache = ignore_cats_cache)

            if len(self.filtered_data) == 0:
                self.logger.warning("No data was found with applied filters!")
        else:
            self.filtered_data = self.data

        self._search_database_keys(
            query=query,
            search_results_n=search_results_n,
            similarity_search_type=similarity_search_type,
            similarity_params=similarity_params,
            perform_similarity_search=perform_similarity_search,
        )

        results = self._get_dict_results(return_keys_list=return_keys_list)

        # resetting search
        self.filtered_data = None
        self.keys_list = None
        self.results_keys = None

        return results

    async def search_database_async(
        self,
        query: str = None,
        search_results_n: int = None,
        llm_search_keys: list = None,
        keyword_check_keys: list = None,
        keyword_check_cutoff: float = None,
        filter_criteria: dict = None,
        similarity_search_type: str = None,
        similarity_params: dict = None,
        perform_similarity_search: bool = None,
        ignore_cats_cache : bool = None,
        return_keys_list: list = None,
        database_name: str = None,
    ) -> list:
        """
        Searches through keys and retrieves specified fields from the search results
        in the mock database for a given filter.
        """

        if query is None:
            perform_similarity_search = False

        if ignore_cats_cache is None:
            ignore_cats_cache = self.ignore_cats_cache

        if self.mdbc_h:

            mdbc_input = {}

            if database_name:
                mdbc_input["database_name"] = database_name

            mdbc_input.update(
                {
                    "query": query,
                    "search_results_n": search_results_n,
                    "llm_search_keys": llm_search_keys,
                    "keyword_check_keys": keyword_check_keys,
                    "keyword_check_cutoff": keyword_check_cutoff,
                    "filter_criteria": filter_criteria,
                    "similarity_search_type": similarity_search_type,
                    "similarity_params": similarity_params,
                    "perform_similarity_search": perform_similarity_search,
                    "return_keys_list": return_keys_list,
                    "database_name": database_name,
                }
            )

            return self.mdbc_h.search_data(**mdbc_input)

        if filter_criteria:
            temp = self._filter_database(
                filter_criteria=filter_criteria,
                llm_search_keys=llm_search_keys,
                keyword_check_keys=keyword_check_keys,
                keyword_check_cutoff=keyword_check_cutoff,
            )

            await self._filter_llm_async(**temp, ignore_cats_cache = ignore_cats_cache)

            if len(self.filtered_data) == 0:
                self.logger.warning("No data was found with applied filters!")
        else:
            self.filtered_data = self.data

        self._search_database_keys(
            query=query,
            search_results_n=search_results_n,
            similarity_search_type=similarity_search_type,
            similarity_params=similarity_params,
            perform_similarity_search=perform_similarity_search,
        )

        results = self._get_dict_results(return_keys_list=return_keys_list)

        # resetting search
        self.filtered_data = None
        self.keys_list = None
        self.results_keys = None

        return results

    def remove_from_database(
        self, filter_criteria: dict = None, database_name: str = None
    ):
        """
        Removes key-value pairs from a dictionary based on filter criteria.
        """

        if self.mdbc_h:

            if database_name is None:
                raise ValueError("Missing database_name input for remote MockerDB!")

            mdbc_input = {
                "filter_criteria": filter_criteria,
                "database_name": database_name,
            }

            return self.mdbc_h.delete_data(**mdbc_input)

        if filter_criteria is None:
            filter_criteria_list = []
        else:
            filter_criteria_list = self._prep_filter_criterias(
                filter_criteria=filter_criteria
            )

        self.data = {
            key: value
            for key, value in self.data.items()
            if not any(
                all(value.get(k) == v for k, v in filter_criteria.items())
                for filter_criteria in filter_criteria_list
            )
        }

        self.save_data()

    def embed_texts(self, texts: list, embedding_model: str = None):
        """
        Embed list of text.
        """

        if self.mdbc_h:

            mdbc_input = {"texts": texts, "embedding_model": embedding_model}

            return self.mdbc_h.embed_texts(**mdbc_input)

        if embedding_model:
            self.logger.warning(
                "Parameter embedding_model will be ignore, define it when initializing embedder locally!"
            )

        insert = [{"text": text} for text in texts]

        self.insert_values(
            values_dict_list=insert, var_for_embedding_name="text", embed=True
        )

        embeddings = [
            self.search_database(
                query=query, return_keys_list=["embedding"], search_results_n=1
            )[0]["embedding"].tolist()
            for query in texts
        ]

        return {"embeddings": embeddings}

    def show_handlers(self):
        """
        Show active handlers in MockerDB API.
        """

        if self.mdbc_h:

            return self.mdbc_h.show_handlers()

        raise ValueError("Establish connection to remote MockerDB first!")

    def initialize_database(
        self, database_name: str = "default", embedder_params: dict = None
    ):
        """
        Initialize database handler in MockerDB API.
        """

        if self.mdbc_h:

            return self.mdbc_h.initialize_database(
                database_name=database_name, embedder_params=embedder_params
            )

        raise ValueError("Establish connection to remote MockerDB first!")
