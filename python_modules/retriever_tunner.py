"""
Retriever tunner

A simple tool to compare and tune retriever performance, given a desired ranking to strive for.
The goal is to provide a simple metric to measure how a given retriver is close to the 'ideal', generated for example
with a use of more expensive, slower or simply no-existant method.
"""

import numpy as np
import random
import logging
import attr
from mocker_db import MockerDB

@attr.s
class RetrieverTunner:

    # search pool for calculating metrics
    queries = attr.ib(default=None)
    search_values_list = attr.ib(default=None)

    # rankings for calculating metrics
    ranking_dicts = attr.ib(default=None)
    target_ranking_name = attr.ib(default='all-mpnet-base-v2')
    embedding_model_names = attr.ib(default=['paraphrase-multilingual-mpnet-base-v2','all-mpnet-base-v2'])

    # for similarity search
    sim_search_handlers = attr.ib(default={})
    similarity_search_h_params = attr.ib(default={'processing_type' : 'parallel',
                                                  'max_workers' : 4,
                                                   'tbatch_size' : 1000})
    similarity_search_h = attr.ib(default=MockerDB)
    persist_handlers = attr.ib(default=True)

    # for selecting random queries if not provided
    n_random_queries = attr.ib(default=100)
    seed = attr.ib(default=23)

    # for defining metrics
    metrics_params = attr.ib(default={'n_results' : [3,5,10],
                                      'prep_types' : ['correction', 'ceiling'],
                                      'ratio' : 0.6,
                                      'target_sum' : 1})

    logger = attr.ib(default=None)
    logger_name = attr.ib(default='Similarity search')
    loggerLvl = attr.ib(default=logging.INFO)
    logger_format = attr.ib(default=None)


    def __attrs_post_init__(self):
        self._initialize_logger()
        self._initialize_similarity_search_handlers()
        self._initialize_queries()



    def _initialize_logger(self):

        """
        Initialize a logger for the class instance based on the specified logging level and logger name.
        """

        if self.logger is None:
            logging.basicConfig(level=self.loggerLvl, format=self.logger_format)
            logger = logging.getLogger(self.logger_name)
            logger.setLevel(self.loggerLvl)

            self.logger = logger

    def _initialize_similarity_search_handlers(self):

        for model_name in self.embedding_model_names:

            embedder_params = self.similarity_search_h_params
            # add model name to parameters
            embedder_params['model_name_or_path'] = model_name
            # define handler for each model
            self.sim_search_handlers[model_name] = self.similarity_search_h(persist=self.persist_handlers,
                                                                            file_path=f'./rt_persist_{model_name}',
                                                                            embedder_params = embedder_params)

    def _initialize_queries(self):

        if self.queries is None:
            self.queries = self._select_random_queries()


    def _select_random_queries(self,
                               search_values_list : list = None,
                               n : int = None,
                               seed : int = None):

        if search_values_list is None:
            search_values_list = self.search_values_list

        if n is None:
            n = self.n_random_queries

        if seed is None:
            seed = self.seed

        if seed is not None:
            random.seed(seed)

        # Ensure n is not larger than the length of the list
        n = min(n, len(search_values_list))

        return random.sample(search_values_list, n)

    def _get_ranking_i(self, handler, query, insert_size):

        hh = handler.search_database(query=query,
                                    return_keys_list=['id'],
                                    search_results_n=insert_size)

        return [ i['id'] for i in hh]

    def construct_ranking(self,
                          queries : list,
                          search_values_list : list,
                          handler) -> dict:


        # establish size of inserts
        insert_size = len(search_values_list)

        # construct insert dict
        insert_dict = [{'id' : i, 'text' : search_values_list[i]} for i in range(insert_size)]

        # insert values into handler
        handler.insert_values(values_dict_list=insert_dict,
                                        var_for_embedding_name='text')


        # construct ranking dict
        ranking_dict = {query : self._get_ranking_i(handler = handler,
                                                    query=query,
                                                    insert_size=insert_size) for query in queries}



        return ranking_dict


    def construct_rankings(self,
                           queries : list = None,
                           search_values_list : list = None,
                           model_names : list = None,
                           handlers = None):

        if queries is None:
            queries = self.queries

        if search_values_list is None:
            search_values_list = self.search_values_list

        if model_names is None:
            model_names = self.embedding_model_names

        if handlers is None:
            handlers = self.sim_search_handlers

        self.ranking_dicts = {model_name : self.construct_ranking(queries = queries,
                                                search_values_list = search_values_list,
                                                handler = handlers[model_name]) for model_name in model_names}





    def _substruct_lists_with_correction(self, list1, list2):
        return [abs(b - a)  for a, b in zip(list1, list2)]

    def _substruct_lists_with_ceiling(self, list1, list2, ceiling = 10):
        return [min(ceiling,abs(b - a))  for a, b in zip(list1, list2)]

    def _generate_decreasing_weights(self, n, target_sum=1, ratio=0.8):

        if n <= 0:
            return []

        elements = [target_sum * (ratio ** i) for i in range(n)]
        sum_elements = sum(elements)

        # Normalize the elements to sum up to 1
        normalized_elements = [el / sum_elements for el in elements]

        return normalized_elements

    def _apply_weights_to_score(self, preped_list,weights):

        dot_product = sum(a * b for a, b in zip(preped_list, weights))

        return dot_product


    def calculate_score(self,
                        id,
                        target_ranking_list,
                        compared_ranking_list,
                        ratio = 0.6,
                        target_sum=1,
                        ceiling = 10,
                        prep_type = 'correction'):

        if prep_type == 'correction':

            preped_list = self._substruct_lists_with_correction(target_ranking_list[id], compared_ranking_list[id])

        if prep_type == 'ceiling':

            preped_list = self._substruct_lists_with_ceiling(target_ranking_list[id], compared_ranking_list[id], ceiling=ceiling)

        decresing_weights = self._generate_decreasing_weights(n = len(preped_list), target_sum=target_sum, ratio=ratio)

        score = self._apply_weights_to_score(preped_list = preped_list,weights = decresing_weights)

        return score

    def make_scores_dict(self,
                         target_ranking = None,
                         compared_rankings = None,
                         n_results = None,
                         prep_types = None,
                         ratio = None,
                         target_sum = None):

        if ratio is None:
            ratio = self.metrics_params['ratio']
        if target_sum is None:
            target_sum = self.metrics_params['target_sum']
        if n_results is None:
            n_results = self.metrics_params['n_results']
        if prep_types is None:
            prep_types = self.metrics_params['prep_types']

        if target_ranking is None:
            target_ranking = self.ranking_dicts[self.target_ranking_name]
        if compared_rankings is None:
            compared_rankings = {ranking : self.ranking_dicts[ranking] for ranking in self.embedding_model_names \
                if ranking != self.target_ranking_name}


        comparison_list_dict = {}
        compared_scores_dict = {}

        for compared_ranking_name in compared_rankings:

            record_key = self.target_ranking_name + '|' + compared_ranking_name
            compared_scores_dict[record_key] = {}

            n_results.append(len(target_ranking))

            for n_result in n_results:
                for prep_type in prep_types:


                    comparison_list_dict[record_key] = [self.calculate_score(id = ranking_id,
                                                                                target_ranking_list = target_ranking,
                                                                                compared_ranking_list = compared_rankings[compared_ranking_name],
                                                                                prep_type=prep_type,
                                                                                ceiling=n_result,
                                                                                ratio=ratio,
                                                                                target_sum=target_sum) \
                                                        for ranking_id in target_ranking.keys()]


                    compared_scores_dict[record_key]['mean' + str(n_result) + prep_type] = np.mean(comparison_list_dict[record_key])

        return compared_scores_dict

