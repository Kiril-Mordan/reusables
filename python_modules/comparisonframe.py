"""
Comparison Frame is designed to automate and streamline the process of comparing textual data, particularly focusing on various metrics
such as character and word count, punctuation usage, and semantic similarity.
It's particularly useful for scenarios where consistent text analysis is required,
such as evaluating the performance of natural language processing models, monitoring content quality,
or tracking changes in textual data over time using manual evaluation.
"""

import numpy as np #==1.26.0
import string
import logging
from collections import Counter
from datetime import datetime #==5.2
import pandas as pd #==2.1.1
import attrs #>=23.2.0
from mocker_db import MockerDB #==0.2.1


# Metadata for package creation
__package_metadata__ = {
    "author": "Kyrylo Mordan",
    "author_email": "parachute.repo@gmail.com",
    "description": "A simple tool to compare textual data against validation sets.",
    # Add other metadata as needed
}

@attrs.define
class RecordsAnalyser:

    """
    Calculates metrics and scores based on records in comparisonframe.
    """

    mocker_h =  attrs.field(default = None)

    compare_scores = attrs.field(default = ['char_count_diff',
                                        'word_count_diff',
                                        'line_count_diff',
                                        'punctuation_diff',
                                        'semantic_similarity'])

    aggr_scores = attrs.field(default = ['min', 
                                         'p25',
                                         'median',
                                         'mean',
                                         'p75',
                                         'max'])

    # Logger settings
    logger =  attrs.field(default=None)
    logger_name =  attrs.field(default='RecordsAnalyser')
    loggerLvl =  attrs.field(default=logging.INFO)

    def __attrs_post_init__(self):
        self._initialize_logger()


    def _initialize_logger(self):

        """
        Initialize a logger for the class instance based on
        the specified logging level and logger name.
        """

        if self.logger is None:
            logging.basicConfig(level=self.loggerLvl)
            logger = logging.getLogger(self.logger_name)
            logger.setLevel(self.loggerLvl)

            self.logger = logger

    def calculate_score(self, method_name : str, *args, **kwargs):

        """
        Calculates any available score.
        """

        method = getattr(self, method_name, None)
        if callable(method):
            return method(*args, **kwargs)
        else:
            raise AttributeError(f"Method '{method_name}' not found")

    def calculate_scores(self, method_names : list = None, *args, **kwargs):

        """
        Calculates dictionary of available scores.
        """

        if method_names is None:
            method_names = self.compare_scores

        scores = {}

        scores = {method_name : self.calculate_score(
            method_name = method_name,
            *args, 
            **kwargs) for method_name in method_names}
        
        return scores

    def calculate_aggr_scores(self, method_names : list = None, *args, **kwargs):

        """
        Calculates dictionary of available aggr scores.
        """

        if method_names is None:
            method_names = self.aggr_scores


        scores = self.calculate_scores(method_names = method_names, 
                              *args, **kwargs)

        scores_output = {}
        for key in scores:
            scores_output.update(scores[key])


        return scores_output


    def char_count_diff(self, exp_text, prov_text):

        """
        Calculates the absolute difference in the number of characters between two texts.
        """

        return abs(len(exp_text) - len(prov_text))

    def word_count_diff(self, exp_text, prov_text):

        """
        Calculates the absolute difference in the number of words between two texts.
        """

        return abs(len(exp_text.split()) - len(prov_text.split()))

    def line_count_diff(self, exp_text, prov_text):

        """
        Calculates the absolute difference in the number of lines between two texts.
        """

        return abs(len(exp_text.splitlines()) - len(prov_text.splitlines()))

    def punctuation_diff(self, exp_text, prov_text):

        """
        Calculates the total difference in the use of punctuation characters between two texts.
        """

        punctuation1 = Counter(char for char in exp_text if char in string.punctuation)
        punctuation2 = Counter(char for char in prov_text if char in string.punctuation)
        return sum((punctuation1 - punctuation2).values()) + sum((punctuation2 - punctuation1).values())


    def semantic_similarity(self, exp_text, prov_text):

        """
        Computes the semantic similarity between two pieces of text using their embeddings.
        """


        self.mocker_h.insert_values(values_dict_list = [
            {"text" : exp_text}
            ],
            var_for_embedding_name = 'text',
            embed = True)

        self.mocker_h.search_database(
            query = prov_text,
            filter_criteria = {
                "text" : exp_text
            }
        )

        distance = self.mocker_h.results_dictances

        return distance[0].item()

    def min(self, df):

        """
        Min values for each column in dataframe.
        """

        df = df.copy()
        df.columns = ["min_" + col for col in df.columns]

        return df.agg(lambda x: x.min()).to_dict()

    def max(self, df):

        """
        Max values for each column in dataframe.
        """

        df = df.copy()
        df.columns = ["max_" + col for col in df.columns]
        
        return df.agg(lambda x: x.max()).to_dict()

    def mean(self, df):

        """
        Mean values for each column in dataframe.
        """

        df = df.copy()
        df.columns = ["mean_" + col for col in df.columns]
        
        return df.agg(lambda x: x.mean()).to_dict()

    def median(self, df):

        """
        Median values for each column in dataframe.
        """

        df = df.copy()
        df.columns = ["median_" + col for col in df.columns]
        
        return df.agg(lambda x: x.median()).to_dict()

    def p25(self, df):

        """
        Percentile 25 values for each column in dataframe.
        """

        df = df.copy()
        df.columns = ["p25_" + col for col in df.columns]
        
        return df.agg(lambda x: x.quantile(0.25)).to_dict()

    def p75(self, df):

        """
        Percentile 75 values for each column in dataframe.
        """

        df = df.copy()
        df.columns = ["p75_" + col for col in df.columns]
        
        return df.agg(lambda x: x.quantile(0.75)).to_dict()


@attrs.define
class ComparisonFrame:

    """
    Comparison Frame is designed to automate and streamline the process of comparing textual data, particularly focusing on various metrics
    such as character and word count, punctuation usage, and semantic similarity.
    It's particularly useful for scenarios where consistent text analysis is required,
    such as evaluating the performance of natural language processing models, monitoring content quality,
    or tracking changes in textual data over time using manual evaluation.
    """

    # MockerDB related parameters

    ## mocker default parameters
    mocker_params = attrs.field(default = {
        'file_path' : "./comparisonframe_storage",
         'persist' : True})

    ## scores to calculate
    compare_scores = attrs.field(default = None)
    aggr_scores = attrs.field(default = None)
    test_query = attrs.field(default = None)
    
    
    ## dependencies
    mocker_h_class = attrs.field(default = MockerDB)
    records_analyser_class = attrs.field(default = RecordsAnalyser)
    ## activated dependecies
    mocker_h = attrs.field(default=None)
    records_analyser = attrs.field(default=None)

    # Logger settings
    logger = attrs.field(default=None)
    logger_name = attrs.field(default='ComparisonFrame')
    loggerLvl = attrs.field(default=logging.INFO)

    def __attrs_post_init__(self):
        self._initialize_logger()
        self._initialize_mocker()
        self._initialize_records_analyser()

    def _initialize_logger(self):

        """
        Initialize a logger for the class instance based on
        the specified logging level and logger name.
        """

        if self.logger is None:
            logging.basicConfig(level=self.loggerLvl)
            logger = logging.getLogger(self.logger_name)
            logger.setLevel(self.loggerLvl)

            self.logger = logger



    def _initialize_mocker(self):

        """
        Initializes an instance of mockerdb if wasn't initialized already.
        """
        if self.mocker_h is None:

            self.mocker_h = self.mocker_h_class(**self.mocker_params,
            logger = self.logger)

        self.mocker_h.establish_connection()

    def _initialize_records_analyser(self):

        """
        Initializes records analyser.
        """

        self.records_analyser = self.records_analyser_class(
            mocker_h = self.mocker_h
        )

    def _merge_lists_by_key_full_left(self, list1 : list, list2 : list, key : str):
        # Create a dictionary for quick lookup from list2
        dict2 = {item[key]: item for item in list2}

        # Iterate over list1 and merge with corresponding dict2 item if exists
        merged_list = []
        for item in list1:
            run_id = item[key]
            if run_id in dict2:
                # If the run_id is in dict2, merge dictionaries
                merged_item = {**item, **dict2[run_id]}
            else:
                # If the run_id is not in dict2, use item as is
                merged_item = item
            merged_list.append(merged_item)

        return merged_list

    def _call_comparer(self, record_run, timestamp, compare_scores):

        if record_run.get('run_id', None) and record_run.get('record_id', None):

            comparison = {"collection" : "scores",
                            "table" : "runs",
                            "timestamp" : timestamp,
                            "record_id" : record_run['record_id'],
                            "run_id": record_run['run_id']}

            comparison_scores = self.records_analyser.calculate_scores(
                method_names = compare_scores, 
                exp_text = record_run['expected_text'],
                prov_text = record_run['provided_text'])
            
            comparison.update(comparison_scores)

        return comparison


### RECORDING QUERIES AND RUNS

    def record_queries(self, 
                     queries : list, 
                     expected_texts : list, 
                     metadata : dict = {}):

        """
        Records a new query and its expected result in the record file.
        """

        # Check if queries and expected texts are lists of same lenght
        # or one of them is a single value
        if (len(queries) != len(expected_texts)) and \
            not (((len(queries) == 1) and (len(expected_texts) != 1)) or\
                ((len(queries) != 1) and (len(expected_texts) == 1))):
            raise ValueError(f"Queries len: {len(queries)}, Expected texts len: {len(expected_texts)}")

        if (len(queries) != len(expected_texts)) and (len(queries) == 1):
             queries = [queries[0] for _ in expected_texts]

        if (len(queries) != len(expected_texts)) and (len(expected_texts) == 1):
             expected_texts = [expected_texts[0] for _ in queries]


        restricted_keys = ['collection', 'table', 'record_id', 'text', 'query'] 

        # Check if any of the restricted keys are in the metadata
        if any(key in metadata for key in restricted_keys):
            raise ValueError(f"Metadata contains restricted keys: {[key for key in restricted_keys if key in metadata]}")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        insert_queries = [{"collection" : "records",
                                "table" : "queries",
                                "text" : query,
                                **metadata} \
                                    for query in queries]

        insert_expected_text = [{"collection" : "records",
                                "table" : "expected_text",
                                "query" : query,
                                "text" : expected_text,
                                **metadata} \
                                    for query, expected_text in zip(queries,expected_texts)]

        inserts = insert_queries + insert_expected_text #+ insert_entries

        self.mocker_h.insert_values(values_dict_list = inserts,
                                    var_for_embedding_name = 'text',
                                    embed = True)


    def record_runs(self, 
                   queries : list,
                   provided_texts : list,
                   metadata : dict = {}):

        """
        Recods run of provided text for a given query.
        """

        # Check if queries and expected texts are lists of same lenght
        # or one of them is a single value
        if (len(queries) != len(provided_texts)) and \
            not (((len(queries) == 1) and (len(provided_texts) != 1)) or\
                ((len(queries) != 1) and (len(provided_texts) == 1))):
            raise ValueError(f"Queries len: {len(queries)}, Provided texts len: {len(expected_texts)}")

        if (len(queries) != len(provided_texts)) and (len(queries) == 1):
             queries = [queries[0] for _ in provided_texts]

        if (len(queries) != len(provided_texts)) and (len(provided_texts) == 1):
             provided_texts = [provided_texts[0] for _ in queries]


        restricted_keys = ['collection', 'table', 'run_id', 'text', 'query',"timestamp"] 

        # Check if any of the restricted keys are in the metadata
        if any(key in metadata for key in restricted_keys):
            raise ValueError(f"Metadata contains restricted keys: {[key for key in restricted_keys if key in metadata]}")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        insert_provided_text = [{"collection" : "runs",
                                "table" : "provided_text",
                                "timestamp" : timestamp,
                                "query" : query,
                                "text" : provided_text,
                                **metadata} \
                                    for query, provided_text in zip(queries,provided_texts)]

        inserts = insert_provided_text

        self.mocker_h.insert_values(values_dict_list = inserts,
                                    var_for_embedding_name = 'text',
                                    embed = True)

### EXTRACTING TABLES

    def get_all_queries(self, 
        metadata_filters = None
        ):

        """
        Retrieves a list of all recorded queries, with optional filters.
        """

        filter_criteria = {"collection" : "records",
                                "table" : "queries"}

        if metadata_filters:
            filter_criteria.update(metadata_filters)

        # if untested_only:
        #     filter_criteria['tested'] = None

        queries_records = self.mocker_h.search_database(
            filter_criteria = filter_criteria,
            perform_similarity_search = False,
            return_keys_list = ['text'])

        queries = [record['text'] for record in queries_records]

        return queries


    def get_all_records(self, 
                        queries : list = None,
                        metadata_filters : dict = {}):

        """
        Retrieves a list of records, with optional filters.
        """


        if queries is None:
            queries_records = self.mocker_h.search_database(
                filter_criteria = {"collection" : "records",
                                    "table" : "queries",
                                    **metadata_filters},
                                    perform_similarity_search = False,
                                    return_keys_list = ['text','+&id'])
        else:
            queries_records = self.mocker_h.search_database(
                filter_criteria = {"collection" : "records",
                                    "table" : "queries",
                                    "text" : queries,
                                    **metadata_filters},
                                    perform_similarity_search = False,
                                    return_keys_list = ['text','+&id'])

        queries = [query['text'] for query in queries_records]

        expected_text_records = self.mocker_h.search_database(
            filter_criteria = {"collection" : "records",
                                "table" : "expected_text",
                                "query" : queries,
                                **metadata_filters},
                                perform_similarity_search = False,
                                return_keys_list = ['+&id','query', 'text'])

        
        # record ids will be added based mocker hash keys after mocker is updated with that ability

        if expected_text_records:

            updated_list_of_dicts = [
                {**{
                    'expected_text' if k == 'text' else 
                    'record_id' if k == '&id' else k: v
                    for k, v in dictionary.items()
                }}
                for dictionary in expected_text_records
            ]

        else:
            updated_list_of_dicts = []

        return updated_list_of_dicts

    def get_all_records_df(self, 
                          queries : list = None,
                          metadata_filters : dict = {}):

        """
        Retrieves records dataframe, with optional filters.
        """

        return pd.DataFrame(self.get_all_records(
            queries=queries,
            metadata_filters=metadata_filters))

    def get_all_runs(self, 
                     queries : list = None,
                     run_ids : list = None):

        """
        Retrieves run lists for selected filters.
        """


        filter_criteria={
                    "collection" : "runs",
                    "table" : "provided_text"
                }

        if queries:
            filter_criteria["query"] = queries

        if run_ids:
            filter_criteria["&id"] = run_ids

        run_records = self.mocker_h.search_database(
            filter_criteria=filter_criteria,
            perform_similarity_search = False,
            return_keys_list = ['+&id', 
                                'query',
                                'text',
                                'timestamp'])
            
        if run_records:

            updated_list_of_dicts = [
                {**{'provided_text' if k == 'text' else 
                    'run_id' if k == '&id' else k: v
                    for k, v in dictionary.items()}}
                for dictionary in run_records
            ]

        else:
            updated_list_of_dicts = []

        return updated_list_of_dicts
        
    def get_all_runs_df(self, 
                        queries : list = None,
                        run_ids : list = None):

        """
        Retrieves dataframe of runs for selected filters.
        """

        df = pd.DataFrame(self.get_all_runs(
            queries=queries,
            run_ids=run_ids))
   
        return df.replace({np.nan: None})


    def get_all_run_scores(self, 
                           queries : list = None,
                           run_ids : list = None,
                           comparison_ids : list = None):

        """
        Retrieves list of comparison scores for selected filters.
        """


        filter_criteria={
                    "collection" : "runs",
                    "table" : "provided_text"
                }

        filter_criteria2={
                    "collection" : "scores",
                    "table" : "runs"
                }

        if queries:
            filter_criteria["query"] = queries
        if run_ids:
            filter_criteria["run_id"] = run_ids
        if comparison_ids:
            filter_criteria2["&id"] = comparison_ids

        run_records = self.mocker_h.search_database(
            filter_criteria=filter_criteria,
            perform_similarity_search = False,
            return_keys_list = ['+&id', 
                                'query',
                                'text',
                                'timestamp'])

        run_ids = [run['&id'] for run in run_records]

        filter_criteria2["run_id"] = run_ids

        scores = self.mocker_h.search_database(
            filter_criteria = filter_criteria2,
                                perform_similarity_search = False,
                                return_keys_list = ['+&id',
                                '-collection', '-table'])

        if scores:
            
            run_records = [
                {**{'provided_text' if k == 'text' else 
                    'run_id' if k == '&id' else k: v
                    for k, v in dictionary.items()}}
                for dictionary in run_records
            ]

            scores = [
                {**{'comparison_id' if k == '&id' else k: v
                    for k, v in dictionary.items()}}
                for dictionary in scores
            ]
            
            updated_list_of_dicts = self._merge_lists_by_key_full_left(
                 run_records, scores, "run_id")

            

        else:
            updated_list_of_dicts = []

        return updated_list_of_dicts

    def get_all_run_scores_df(self, 
                              queries : list = None, 
                              run_ids : list = None,
                              comparison_ids : list = None):

        """
        Retrieves dataframe of comparison scores for selected filters.
        """

        return pd.DataFrame(self.get_all_run_scores(
            queries = queries,
            run_ids = run_ids,
            comparison_ids = comparison_ids))

    
    def get_all_aggr_scores(self, 
                           queries : list = None):

        """
        Retrieves list for aggregate scores for selected filters.
        """


        filter_criteria={
                    "collection" : "scores",
                    "table" : "records"
                }

        if queries:
            filter_criteria["query"] = queries


        scores = self.mocker_h.search_database(
            filter_criteria=filter_criteria,
            perform_similarity_search = False,
            return_keys_list = ['+&id', '-collection', '-table'])


        if scores:
            
            scores = [
                {**{'record_status_id' if k == '&id' else k: v
                    for k, v in dictionary.items()}}
                for dictionary in scores
            ]
                        
        else:
            scores = []

        return scores

    def get_all_aggr_scores_df(self, 
                              queries : list = None):

        """
        Retrieves dataframe for aggregate scores for selected filters.
        """
        return pd.DataFrame(self.get_all_aggr_scores(
            queries = queries))

    def get_test_statuses(self, 
                          queries : list = None):

        """
        Retrieves list of test statuses for selected filters.
        """


        filter_criteria={
                    "collection" : "scores",
                    "table" : "status"
                }

        if queries:
            filter_criteria["query"] = queries


        statuses = self.mocker_h.search_database(
            filter_criteria=filter_criteria,
            perform_similarity_search = False,
            return_keys_list = ['-collection', '-table'])

        return statuses

    def get_test_statuses_df(self, 
                          queries : list = None):
        """
        Retrieves dataframe for test statuses for selected filters.
        """
        return pd.DataFrame(self.get_test_statuses(queries=queries))

### CALCULATING COMPARISON AND AGGREGATE SCORES

    def compare_runs_with_records(self,                        
                            queries : list = None,
                            compare_scores : list = None,
                            latest_runs : bool = True):

        """
        Compares the provided text with all recorded expected results 
        for a specific query and stores the comparison results.

        Parameters:
            queries : list - queries from compare scores table
            compare_scores : list - compare scores to calculate
            latest_runs : bool - condition that selects only new runs
                for which comparison scores do not exist yet
        """

        if compare_scores is None:
            compare_scores = self.compare_scores

        if latest_runs:

            # pulling scores to determine which runs not to use again
            scores = self.get_all_run_scores()
            run_ids_to_exclude = [score['run_id'] for score in scores \
                if score.get('record_id', False)]


            # pull all runs
            runs_all = self.get_all_runs(queries=queries)

            run_ids = [run['run_id'] for run in runs_all \
                if run['run_id'] not in run_ids_to_exclude]

            # pull relevant runs
            runs = self.get_all_runs(queries=queries,
                                    run_ids=run_ids)
        else:
            # pull relevant runs
            runs = self.get_all_runs(queries=queries)


        # pull relevant records
        records = self.get_all_records(queries=queries)


        records_runs = self._merge_lists_by_key_full_left(
            list1 = runs,
            list2 = records, 
            key = "query")

        if not records_runs:
            raise ValueError("Query not found in records.")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        comparisons = [self._call_comparer(record_run, 
                                timestamp, 
                                compare_scores) for record_run in records_runs]

        if comparisons:

            self.mocker_h.insert_values(values_dict_list = comparisons,
                                        embed = False)
        else:
            self.logger.warning("No comparisons were completed for queries!")

    def calculate_aggr_scores(self,
                            queries : list = None,
                            compare_scores : list = None,
                            aggr_scores : list = None,
                            latest_runs : bool = True
                            ):

        """
        Calculate aggr scores for selected queries based on compare scores.

        Parameters:
            queries : list - queries from compare scores table
            compare_scores : list - compare scores to use for 
                calculating aggregate scores
            aggr_scores : list - names of aggregate scores from pre defined
            latest_runs : bool - condition that selects only new compare
                scores for which aggregate scores do not exist yet
        """

        if compare_scores is None:
            compare_scores = self.compare_scores

        if compare_scores is None:
            compare_scores = self.records_analyser.compare_scores

        if aggr_scores is None:
            aggr_scores = self.aggr_scores

        if aggr_scores is None:
            aggr_scores = self.records_analyser.aggr_scores

        if latest_runs:

            # pulling scores to determine which runs not to use again
            scores = self.get_all_aggr_scores()
            run_scores = self.get_all_run_scores(queries=queries)

            comparison_ids = [d['comparison_id'] for d in run_scores if d.get('comparison_id', None)]

            exclusion_cid = []

            for sc in scores:
                exclusion_cid += sc['comparison_id']

            comparison_ids = [cid for cid in comparison_ids if cid not in exclusion_cid]

            if comparison_ids:

                # pull relevant runs
                df = self.get_all_run_scores_df(
                    queries=queries,
                    comparison_ids=comparison_ids)
            else:
                df = pd.DataFrame([])
        else:
            # pull relevant runs
            df = self.get_all_run_scores_df(
                queries=queries)

        # scores = self.get_all_aggr_scores()
        comparisons = []
        if df.shape[0]>0:

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # get relevant queries
            queries = list(set(df['query']))

            for query in queries:

                df_limited = df.query(f"query == '{query}'")
                
                # get score dataframe for each query
                df_scores = df_limited[compare_scores]

                comparison_ids = df_limited['comparison_id'].to_list()

                comparison_ids = [cid for cid in comparison_ids if not pd.isna(cid)]

                comparison = {"collection" : "scores",
                                    "table" : "records",
                                    "timestamp" : timestamp,
                                    "comparison_id" : comparison_ids,
                                    "query": query}

                comparison_scores = self.records_analyser.calculate_aggr_scores(
                    method_names = aggr_scores,
                    df = df_scores
                )

                comparison.update(comparison_scores)
                comparisons.append(comparison)

        if comparisons:

            self.mocker_h.insert_values(values_dict_list = comparisons,
                                        embed = False)
        else:
            self.logger.warning("No comparisons were completed for queries!")

    def calculate_test_statuses(self,
                            test_query : str,
                            queries : list = None
                            ):

        """
        Calculates test statuses for selected queries and 
        test condition.

        Parameters:
            queries : list - queries from aggr scores table
            test_query : str - condition based on aggregate scores
                for latest score
        """

        if test_query is None:
            test_query = self.test_query
        if test_query is None:
            raise ValueError("Provide test query!")


        # pull relevant runs
        df = self.get_all_aggr_scores_df(
                queries=queries)


        comparisons = []
        if df.shape[0]>0:

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            queries = list(set(df['query']))

            for query in queries:

                record_id_d = self.get_all_records(queries=[query])
                
                if record_id_d:
                    record_id = record_id_d[0]['record_id']
                else:
                    raise ValueError(f"No record in records for query: {query}")

                df_sorted = df.query(f"query == '{query}'")\
                    .sort_values(by='timestamp', ascending=False).head(1)

                status = df_sorted.query(test_query).shape[0] > 0
                

                comparison = {"collection" : "scores",
                                "table" : "status",
                                "timestamp" : timestamp,
                                "record_id" : record_id,
                                "record_status_id" : df_sorted['record_status_id'][0],
                                "query": query,
                                "test" : test_query,
                                "valid" : status}

                comparisons.append(comparison)

        if comparisons:

            self.mocker_h.insert_values(values_dict_list = comparisons,
                                        embed = False)
        else:
            self.logger.warning("No comparisons were completed for queries!")

### FLUSHING 
    def flush_records(self,
                      queries : list = None,
                      record_ids : list = None,
                      expected_texts : list = None):

        """
        Removes selected records, all if no filters provided.

        Parameters:
            queries : list 
            record_ids : list
            expected_texts : list
        """

        filter_criterias = {
            "collection" : "records",
            "table" : "queries"
        }

        if queries:
            filter_criterias['query'] = queries
        if record_ids:
            filter_criterias['record_id'] = record_ids
        if expected_texts:
            filter_criterias['expected_text'] = expected_texts

        self.mocker_h.remove_from_database(
            filter_criteria=filter_criterias)

    def flush_runs(self,
                    queries : list = None,
                    run_ids : list = None,
                    provided_texts : list = None,
                    timestamps : list = None):

        """
        Removes selected runs, all if no filters provided.

        Parameters:
            queries : list 
            run_ids : list
            provided_texts : list
            timestamps : list
        """

        filter_criterias = {
            "collection" : "runs",
            "table" : "provided_text"
        }

        if queries:
            filter_criterias['query'] = queries
        if run_ids:
            filter_criterias['run_id'] = run_ids
        if provided_texts:
            filter_criterias['provided_text'] = provided_texts
        if timestamps:
            filter_criterias['timestamp'] = timestamps

        self.mocker_h.remove_from_database(
            filter_criteria=filter_criterias)

    def flush_comparison_scores(self,
                    record_ids : list = None,
                    comparison_ids : list = None,
                    queries : list = None,
                    run_ids : list = None,
                    provided_texts : list = None,
                    timestamps : list = None):

        """
        Removes selected comparison results, all if no filters provided.

        Parameters:
            record_ids : list 
            comparison_ids : list
            queries : list
            run_ids : list
            provided_texts : list
            timestamps : list
        """

        filter_criterias = {
            "collection" : "scores",
            "table" : "runs"
        }

        if comparison_ids:
            filter_criterias['comparison_id'] = comparison_ids
        if record_ids:
            filter_criterias['record_id'] = record_ids
        if queries:
            filter_criterias['query'] = queries
        if run_ids:
            filter_criterias['run_id'] = run_ids
        if provided_texts:
            filter_criterias['provided_text'] = provided_texts
        if timestamps:
            filter_criterias['timestamp'] = timestamps

        self.mocker_h.remove_from_database(
            filter_criteria=filter_criterias)

    def flush_aggregate_scores(self,
                    comparison_ids : list = None,
                    queries : list = None,
                    timestamps : list = None):

        """
        Removes selected aggregate scores, all if no filters provided.

        Parameters:
            comparison_ids : list 
            timestamps : list
            queries : list
        """

        filter_criterias = {
            "collection" : "scores",
            "table" : "records"
        }

        if comparison_ids:
            filter_criterias['comparison_id'] = comparison_ids
        if queries:
            filter_criterias['query'] = queries
        if timestamps:
            filter_criterias['timestamp'] = timestamps

        self.mocker_h.remove_from_database(
            filter_criteria=filter_criterias)

    def flush_test_statuses(self,
                    queries : list = None,
                    timestamps : list = None,
                    record_ids : list = None,
                    record_status_ids : list = None,
                    valid : bool = None):

        """
        Removes selected test statuses, all if no filters provided.

        Parameters:
            queries : list 
            timestamps : list
            record_ids : list
            record_status_ids : list
            valid : bool
        """

        filter_criterias = {
            "collection" : "scores",
            "table" : "status"
        }

        if queries:
            filter_criterias['query'] = queries
        if timestamps:
            filter_criterias['timestamp'] = timestamps
        if record_ids:
            filter_criterias['record_id'] = record_ids
        if record_status_ids:
            filter_criterias['record_status_id'] = record_status_ids
        if valid:
            filter_criterias['valid'] = [valid]

        self.mocker_h.remove_from_database(
            filter_criteria=filter_criterias)

        