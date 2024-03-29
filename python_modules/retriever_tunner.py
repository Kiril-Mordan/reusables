"""
Retriever tunner

A simple tool to compare and tune retriever performance, given a desired ranking to strive for.
The goal is to provide a simple metric to measure how a given retriver is close to the 'ideal', generated for example
with a use of more expensive, slower or simply no-existant method.
"""

import numpy as np
import random
import logging
import attr #>=22.2.0
import copy
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from plotly.offline import plot

from mocker_db import MockerDB #==0.0.1

__design_choices__ = {
    'search pool and queries' : ['queries can be provided as a list and augmented with \
        dictionary of filters for each of them',
        "search pool could be provides as a list, at that case will converted \
            into dict with the following keys: 'id','text'",
        "if prepared dictionary is provided, it will be inserted into the mocker"],
    'ranking scores' : ["scores are calculated as result of comparing target ranking and one of compared rankings",
                        "elements compared can be limited, maximum diffrence in ranks could be constrained with ceiling",
                        "weights are applied to emphasise difference between top elements i nthe score"]
}

@attr.s
class RetrieverTunner:

    # search pool for calculating metrics
    queries = attr.ib(default=None)
    queries_filters = attr.ib(default=None)
    search_values_dicts = attr.ib(default=None)
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
                                      'ceilings' : [10],
                                      'prep_types' : ['correction', 'ceiling'],
                                      'weights_ratio' : 0.6,
                                      'weights_sum' : 1,
                                      'inverted' : True})

    # for plotting
    plots_params = attr.ib(default={'top_n' : 3,
                                    'text_lim' : 10,
                                    'alpha' : 0.5,
                                    'save_comp_plot' : False})

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

        """
        Initialize seperate similarity handlers for each of the embedding models.
        """

        for model_name in self.embedding_model_names:

            embedder_params = self.similarity_search_h_params
            # add model name to parameters
            embedder_params['model_name_or_path'] = model_name
            # define handler for each model
            self.sim_search_handlers[model_name] = self.similarity_search_h(persist=self.persist_handlers,
                                                                            file_path=f'./rt_persist_{model_name}',
                                                                            embedder_params = embedder_params)
            self.sim_search_handlers[model_name].establish_connection()

    def _initialize_queries(self):

        """
        Runs on init to select random qureies from the list of pool for search.
        """

        if self.queries is None:
            self.queries = self._select_random_queries()


    def _select_random_queries(self,
                               search_values_list : list = None,
                               n : int = None,
                               seed : int = None):

        """
        Function to select random queries from the list of pool for search.
        """

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

### CONSTRUCT RANKINGS

    def _get_ranking_i(self,
                       handler,
                       query : str,
                       insert_size : int,
                       queries_filter : dict = None):

        """
        Accesses similarity search handler to extract ids.
        """

        hh = handler.search_database(query=query,
                                    return_keys_list=['id'],
                                    search_results_n=insert_size,
                                    filter_criteria = queries_filter)

        return [i['id'] for i in hh]

    def construct_ranking(self,
                          queries : list,
                          queries_filters : dict,
                          search_values_list : list,
                          search_values_dicts : list,
                          handler) -> dict:

        """
        Constructs ranking dictionary of ids based on seached results for selected embeddings model.
        """


        # establish size of inserts
        insert_size = len(search_values_list)

        if search_values_list:


            # construct insert dict
            insert_dict = [{'id' : i, 'text' : search_values_list[i]} for i in range(insert_size)]
        else:
            insert_dict = copy.deepcopy(search_values_dicts)



        # insert values into handler
        handler.insert_values(values_dict_list=insert_dict,
                                        var_for_embedding_name='text')


        # make input for _get_ranking_i
        def fill_get_ranking_i(query,
                               queries_filters = queries_filters,
                               handler = handler,
                               insert_size = insert_size):

            input_dict = {'handler' : handler,
                          'query' : query,
                          'insert_size' : insert_size}

            if queries_filters:
                input_dict['queries_filter'] = queries_filters[query]

            return input_dict

        # construct ranking dict
        ranking_dict = {query : self._get_ranking_i(**fill_get_ranking_i(query = query)) \
            for query in queries}

        return ranking_dict


    def construct_rankings(self,
                           queries : list = None,
                           queries_filters : dict = None,
                           search_values_dicts : dict = None,
                           search_values_list : list = None,
                           model_names : list = None,
                           handlers = None):

        """
        Constructs ranking dictionaries of ids based on seached results for selected embeddings models.
        """

        if queries is None:
            queries = self.queries

        if queries_filters is None:
            queries_filters = self.queries_filters

        if search_values_dicts is None:
            search_values_dicts = self.search_values_dicts

        if search_values_dicts is None:

            if search_values_list is None:
                search_values_list = self.search_values_list
        else:
            search_values_list = None

        if model_names is None:
            model_names = self.embedding_model_names

        if handlers is None:
            handlers = self.sim_search_handlers

        self.ranking_dicts = {model_name : self.construct_ranking(queries = queries,
                                                search_values_dicts = search_values_dicts,
                                                queries_filters = queries_filters,
                                                search_values_list = search_values_list,
                                                handler = handlers[model_name]) for model_name in model_names}


### COMPERISON RANKING SCORES

    def _substruct_lists_with_correction(self,
                                         list1 : list,
                                         list2 : list):

        """
        Calculates absolute difference of ranks for provided lists of target and comparted rankings.
        """

        return [abs(b - a)  for a, b in zip(list1, list2)]

    def _substruct_lists_with_ceiling(self,
                                      list1 : list,
                                      list2 : list,
                                      ceiling : float):

        """
        Calculates absolute difference of ranks for provided lists of target and comparted rankings
        limited by max allowed value.
        """

        return [min(ceiling,abs(b - a))  for a, b in zip(list1, list2)]

    def _normalize_list(self,
                        elem_list : list,
                        norm_type : str):

        """
        Function for normalizing lists with selected method.
        """

        if norm_type == 'min_max':

            max_element = max(max(elem_list),1)

            # Normalize the elements with min max
            return  [el / max_element for el in elem_list]


        if norm_type == 'sum':

            sum_elements = max(sum(elem_list),1)

            # Normalize the elements to sum up to 1
            return [el / sum_elements for el in elem_list]

    def _generate_decreasing_weights(self,
                                     n : int,
                                     target_sum : float = 1,
                                     ratio : float = 0.8):

        """
        Make a list of weights of certain size skewed left or right that sum up to a certain target.
        """

        if n <= 0:
            return []

        elements = [target_sum * (ratio ** i) for i in range(n)]

        normalized_elements = self._normalize_list(elem_list=elements, norm_type='min_max')

        return normalized_elements

    def _apply_weights_to_score(self, preped_list, weights):

        weighted_list = [a * b for a, b in zip(preped_list, weights)]

        normalized_preped_list = self._normalize_list(elem_list=weighted_list, norm_type='sum')

        return sum(normalized_preped_list)


    def calculate_score(self,
                        id : str,
                        target_ranking_list : list,
                        compared_ranking_list : list,
                        weights_ratio : float,
                        weights_sum : float,
                        ceiling : float,
                        n_result : int,
                        prep_type : str):

        """
        Creates a scores for selected permutation of parameter lists
        and compared ranking.
        """

        if prep_type == 'correction':

            preped_list = self._substruct_lists_with_correction(target_ranking_list[id], compared_ranking_list[id])

        if prep_type == 'ceiling':

            preped_list = self._substruct_lists_with_ceiling(target_ranking_list[id], compared_ranking_list[id], ceiling=ceiling)

        decresing_weights = self._generate_decreasing_weights(n = len(preped_list), target_sum=weights_sum, ratio=weights_ratio)

        if n_result:
            preped_list = preped_list[0:n_result]

            sum_decresing_weights = sum(decresing_weights)
            decresing_weights = [el / sum_decresing_weights for el in decresing_weights]

        score = self._apply_weights_to_score(preped_list = preped_list,weights = decresing_weights)

        return score

    def _create_key_for_scores_dict(self,
                                    prefix : str,
                                    n_result : int,
                                    ceiling : float,
                                    prep_type : str):

        return prefix + str(n_result) + "|" + str(ceiling) + "|" + prep_type

    def make_scores_dict(self,
                         target_ranking : dict = None,
                         compared_rankings : dict = None,
                         n_results : list = None,
                         prep_types : list = None,
                         ceilings : list = None,
                         weights_ratio : float = None,
                         weights_sum : float = None,
                         inverted : bool = None):

        """
        Creates a dictiory with all of the inverted distance mean scores for different permutations
        of parameter lists and different compared rankings.
        """


        if n_results is None:
            n_results = self.metrics_params['n_results']
        if prep_types is None:
            prep_types = self.metrics_params['prep_types']

        if ceilings is None:
            ceilings = self.metrics_params['ceilings']
        if weights_ratio is None:
            weights_ratio = self.metrics_params['weights_ratio']
        if weights_sum is None:
            weights_sum = self.metrics_params['weights_sum']


        if target_ranking is None:
            target_ranking = self.ranking_dicts[self.target_ranking_name]
        if compared_rankings is None:
            compared_rankings = {ranking : self.ranking_dicts[ranking] for ranking in self.embedding_model_names \
                if ranking != self.target_ranking_name}

        if inverted is None:
            inverted = self.metrics_params['inverted']


        comparison_list_dict = {}
        compared_scores_dict = {}

        for compared_ranking_name in compared_rankings:

            record_key = self.target_ranking_name + '|' + compared_ranking_name
            compared_scores_dict[record_key] = {}

            ceilings.append(len(target_ranking))
            n_results.append(len(target_ranking))

            for n_result in n_results:
                for ceiling in ceilings:
                    for prep_type in prep_types:


                        comparison_list_dict[record_key] = [self.calculate_score(id = ranking_id,
                                                                                    target_ranking_list = target_ranking,
                                                                                    compared_ranking_list = compared_rankings[compared_ranking_name],
                                                                                    prep_type=prep_type,
                                                                                    ceiling=ceiling,
                                                                                    n_result=n_result,
                                                                                    weights_ratio=weights_ratio,
                                                                                    weights_sum=weights_sum) \
                                                            for ranking_id in target_ranking.keys()]

                        score = np.mean(comparison_list_dict[record_key])

                        prefix = 'irdm|'

                        if inverted:
                            # invert the score so that closer to one is better
                            score = 1 - score
                            prefix = 'rdm|'

                        # create name for inverted distance mean
                        score_name = self._create_key_for_scores_dict(prefix = prefix,
                                                                        n_result = n_result,
                                                                        ceiling = ceiling,
                                                                        prep_type = prep_type)

                        compared_scores_dict[record_key][score_name] = score

        return compared_scores_dict

### PLOT COMPARISON RANKINGS

    def show_model_comparison_plot(self,
                                   ranking_dicts : dict,
                                    target_model : str,
                                    compared_model : str,
                                    top_n : int,
                                    text_lim : int,
                                    alpha : float,
                                    plot_destination : str = None):

        """
        Show plotly scatter plot with target ranking ploted agains selected comparison ranking.
        """


        # Create a Plotly figure
        fig = make_subplots()

        # Add scatter plots for each text
        for text in ranking_dicts[target_model]:
            x_data = ranking_dicts[target_model][text][0:top_n]
            y_data = ranking_dicts[compared_model][text][0:top_n]

            # Ensure the lists are of the same length
            if len(x_data) == len(y_data):
                fig.add_trace(go.Scatter(
                    x=x_data,
                    y=y_data,
                    mode='markers',
                    name=text[0:text_lim],
                    marker=dict(opacity=alpha)
                ))

        # Update layout
        fig.update_layout(
            title=f"Comparison of {target_model} vs {compared_model}",
            xaxis_title=target_model,
            yaxis_title=compared_model
        )

        if plot_destination:
            plot(fig, filename=plot_destination, auto_open=False)

        # Show plot
        fig.show()

    def show_model_comparison_plots(self,
                                ranking_dicts : dict = None,
                               target_model : str = None,
                               compared_models : list = None,
                               top_n : int = None,
                               text_lim : int = None,
                               alpha : float = None,
                               plot_destinations : list = None):

        """
        Show plotly scatter plots with target ranking ploted agains selected comparison rankings.
        """

        if ranking_dicts is None:
            ranking_dicts = self.ranking_dicts
        if target_model is None:
            target_model = self.target_ranking_name
        if compared_models is None:
            compared_models = [model_name for model_name in self.embedding_model_names \
                if model_name != target_model]
        if top_n is None:
            top_n = self.plots_params['top_n']
        if text_lim is None:
            text_lim = self.plots_params['text_lim']
        if alpha is None:
            alpha = self.plots_params['alpha']
        if plot_destinations is None:
            if self.plots_params['save_comp_plot']:
                plot_destinations = ['comp_plot_' + target_model + '|' + model_name for model_name in compared_models]

        i = 0
        for compared_model in compared_models:
            if plot_destinations:
                plot_destination = plot_destinations[i]
            else:
                plot_destination = None

            i = i +1
            self.show_model_comparison_plot(ranking_dicts = ranking_dicts,
                                            target_model = target_model,
                                            compared_model = compared_model,
                                            top_n = top_n,
                                            text_lim = text_lim,
                                            alpha = alpha,
                                            plot_destination = plot_destination)



