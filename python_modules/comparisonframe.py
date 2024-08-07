"""
Comparison Frame is designed to automate and streamline the process of comparing textual data, particularly focusing on various metrics
such as character and word count, punctuation usage, and semantic similarity.
It's particularly useful for scenarios where consistent text analysis is required,
such as evaluating the performance of natural language processing models, monitoring content quality,
or tracking changes in textual data over time using manual evaluation.
"""

import numpy as np
import string
import logging
import uuid
from collections import Counter
from datetime import datetime #==5.2
import pandas as pd #==2.1.1
import attrs #>=23.2.0
from mocker_db import MockerDB #==0.1.2


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
        
        for method_name in method_names:

            scores[method_name] = self.calculate_score(method_name = method_name,
                                        *args, 
                                        **kwargs)

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

            self.mocker_h = self.mocker_h_class(**self.mocker_params)

        self.mocker_h.establish_connection()

    def _initialize_records_analyser(self):

        """
        Initializes records analyser.
        """

        self.records_analyser = self.records_analyser_class(
            mocker_h = self.mocker_h
        )

    def _generate_unique_id(self):
        """
        Generate a unique identifier using UUID4.

        Returns:
            str: A unique identifier as a string.
        """
        return str(uuid.uuid4())


    def record_queries(self, 
                     queries : list, 
                     expected_texts : list, 
                     overwrite : bool = True):

        """
        Records a new query and its expected result in the record file.
        """

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record_id = self._generate_unique_id()

        insert_queries = [{"collection" : "records",
                                "table" : "queries",
                                #"record_id" : record_id,
                                "text" : query} \
                                    for query in queries]

        insert_expected_text = [{"collection" : "records",
                                "table" : "expected_text",
                                #"record_id" : record_id,
                                "query" : query,
                                "text" : expected_text} \
                                    for query, expected_text in zip(queries,expected_texts)]

        # insert_entries = [{"table" : "records",
        #                     "collection" : "test_statuses",
        #                     "record_id" : record_id,
        #                     "timestamp" : timestamp,
        #                     "text" : None,
        #                     "tested" : False,
        #                     "test_status" : None}]

        inserts = insert_queries + insert_expected_text #+ insert_entries

        self.mocker_h.insert_values(values_dict_list = inserts,
                                    var_for_embedding_name = 'text',
                                    embed = True)


    def record_runs(self, 
                   query : str,
                   provided_texts : list):

        """
        Recods run of provided text for a given query.
        """

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        insert_provided_text = [{"collection" : "runs",
                                "table" : "provided_text",
                                "run_id" : self._generate_unique_id(),
                                "timestamp" : timestamp,
                                "query" : query,
                                "text" : provided_text} \
                                    for provided_text in provided_texts]

        inserts = insert_provided_text

        self.mocker_h.insert_values(values_dict_list = inserts,
                                    var_for_embedding_name = 'text',
                                    embed = True)

    # def mark_query_as_tested(self, query, test_status):
    #     """
    #     Updates the 'tested' status and 'test_status' of a specific query in the record file.
    #     """

    #     # Read the existing data
    #     rows = []
    #     with open(self.record_file, mode='r', encoding='utf-8') as file:
    #         reader = csv.reader(file)
    #         rows = list(reader)

    #     headers = rows[0]  # Extract the headers
    #     # Check if 'test_status' is in headers, if not, add it
    #     if 'test_status' not in headers:
    #         headers.append('test_status')

    #     # Find the query and mark it as tested, and update the test status
    #     for row in rows[1:]:  # Skip the header row
    #         if row[2] == query:  # if the query matches
    #             row[4] = 'yes'  # 'yes' indicates tested
    #             if len(row) >= 6:  # if 'test_status' column exists
    #                 row[5] = test_status  # update the 'test_status' column
    #             else:
    #                 row.append(test_status)  # if 'test_status' column doesn't exist, append the status

    #     # Write the updated data back to the file, including the headers
    #     with open(self.record_file, mode='w', newline='', encoding='utf-8') as file:
    #         writer = csv.writer(file)
    #         writer.writerow(headers)  # Write the headers first
    #         writer.writerows(rows[1:])  # Write the data rows


    # def reset_record_statuses(self, record_ids=None):
    #     """
    #     Resets the 'tested' status of specific queries or all queries in the record file, making them available for re-testing.

    #     Parameters:
    #     record_ids (list of int): Optional. A list of record IDs for which to reset the statuses. If None, all records are reset.
    #     """

    #     # Read the existing data
    #     with open(self.record_file, mode='r', encoding='utf-8') as file:
    #         reader = csv.reader(file)
    #         rows = list(reader)

    #     # Check for the right headers and adjust the data rows
    #     headers = rows[0]  # Extract the headers
    #     if 'test_status' not in headers:
    #         headers.append('test_status')  # Add 'test_status' to headers if it's missing

    #     new_rows = [headers]  # Include the headers as the first row

    #     for row in rows[1:]:  # Skip the header row
    #         if record_ids is None or int(row[0]) in record_ids:  # Check if resetting all or specific IDs
    #             new_row = row[:5]  # Select columns 'id' through 'tested'
    #             new_row[4] = 'no'  # 'no' indicates untested
    #             if len(row) == 6:  # if 'test_status' column exists
    #                 new_row.append('')  # reset 'test_status' to an empty string
    #             else:
    #                 new_row.append('')  # if 'test_status' column doesn't exist, still add an empty string placeholder
    #             new_rows.append(new_row)
    #         else:
    #             new_rows.append(row)  # If the ID is not in the list, keep the row unchanged

    #     # Write the updated data back to the file, including the headers
    #     with open(self.record_file, mode='w', newline='', encoding='utf-8') as file:
    #         writer = csv.writer(file)
    #         writer.writerows(new_rows)  # Write the updated rows back to CSV, including headers

    def get_all_queries(self, untested_only : bool = False):

        """
        Retrieves a list of all recorded queries, with an option to return only those that haven't been tested.
        """

        filter_criteria = {"collection" : "records",
                                "table" : "queries"}

        if untested_only:
            filter_criteria['tested'] = None

        queries_records = self.mocker_h.search_database(
            filter_criteria = filter_criteria,
            perform_similarity_search = False,
            return_keys_list = ['text'])

        queries = [record['text'] for record in queries_records]

        return queries

    # def get_comparison_results(self, throw_error : bool = False):

    #     """
    #     Retrieves the comparison results as a DataFrame from the stored file.
    #     """

    #     # Check if the results file exists
    #     if not os.path.isfile(self.results_file):
    #         error_mess = "No results file found. Please perform some comparisons first."
    #         if throw_error:
    #             raise FileNotFoundError(error_mess)
    #         else:
    #             self.logger.error(error_mess)

    #     else:
    #         # Read the CSV file into a pandas DataFrame
    #         df = pd.read_csv(self.results_file)

    #         return df

    def get_all_records(self, queries : list = None):

        """
        Retrieves all query records from the stored file.
        """


        if queries is None:
            queries_records = self.mocker_h.search_database(
                filter_criteria = {"collection" : "records",
                                    "table" : "queries"},
                                    perform_similarity_search = False,
                                    return_keys_list = ['text'])
        else:
            queries_records = self.mocker_h.search_database(
                filter_criteria = {"collection" : "records",
                                    "table" : "queries",
                                    "text" : queries},
                                    perform_similarity_search = False,
                                    return_keys_list = ['text'])

        queries = [query['text'] for query in queries_records]

        expected_text_records = self.mocker_h.search_database(
            filter_criteria = {"collection" : "records",
                                "table" : "expected_text",
                                "query" : queries},
                                perform_similarity_search = False,
                                return_keys_list = ['query', 'text'])

        expected_texts = [et['text'] for et in expected_text_records]

        status_records = self.mocker_h.search_database(
            filter_criteria = {"collection" : "records",
                                "table" : "test_statuses",
                                "query" : queries,
                                "expected_text" : expected_texts},
                                perform_similarity_search = False,
                                return_keys_list = ['query', 
                                                    'expected_text',
                                                    'timestamp',
                                                    'tested',
                                                    'test_status'])

        if status_records:
            updated_list_of_dicts = status_records
        elif expected_text_records:

            updated_list_of_dicts = [
                {**{'expected_text' if k == 'text' else k: v \
                    for k, v in dictionary.items()}, 
                        'timestamp' : None,
                        'tested' : None,
                        'test_status' : None}
                for dictionary in expected_text_records
            ]

        else:
            updated_list_of_dicts = [{
                'query' : None, 
                'expected_text' : None,
                'timestamp' : None,
                'tested' : None,
                'test_status' : None
            }]

        return updated_list_of_dicts

    def get_all_records_scores(self, queries : list = None):

        """
        Retrieves all query records from the stored file.
        """


        if queries is None:
            queries_records = self.mocker_h.search_database(
                filter_criteria = {"collection" : "records",
                                    "table" : "queries"},
                                    perform_similarity_search = False,
                                    return_keys_list = ['text'])
        else:
            queries_records = self.mocker_h.search_database(
                filter_criteria = {"collection" : "records",
                                    "table" : "queries",
                                    "text" : queries},
                                    perform_similarity_search = False,
                                    return_keys_list = ['text'])

        queries = [query['text'] for query in queries_records]

        expected_text_records = self.mocker_h.search_database(
            filter_criteria = {"collection" : "records",
                                "table" : "expected_text",
                                "query" : queries},
                                perform_similarity_search = False,
                                return_keys_list = ['query', 'text'])

        expected_texts = [et['text'] for et in expected_text_records]

        score_records = self.mocker_h.search_database(
            filter_criteria = {"collection" : "scores",
                                "table" : "records",
                                "query" : queries},
                                perform_similarity_search = False)

        scores = [
            {k: v for k, v in d.items() if k not in ["collection",
                                                    "table"]}
            for d in scores
        ]

        if score_records:

            updated_list_of_dicts = [
                {**{'expected_text' if k == 'text' else k: v \
                    for k, v in dictionary.items()}}
                for dictionary in expected_text_records
            ]

            updated_list_of_dicts = self._merge_lists_by_key_full_left(
                 updated_list_of_dicts, score_records, "query")

        elif expected_text_records:

            updated_list_of_dicts = [
                {**{'expected_text' if k == 'text' else k: v \
                    for k, v in dictionary.items()}}
                for dictionary in expected_text_records
            ]

        else:
            updated_list_of_dicts = [{
                'query' : None, 
                'expected_text' : None
            }]

        return updated_list_of_dicts

    def get_all_records_df(self, queries = None):

        """
        Retrieves all query records as a DataFrame from the stored file.
        """

        return pd.DataFrame(self.get_all_records(queries=queries))

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


    def get_all_runs(self, queries : list = None):

        """
        Retrieves all query runs from the stored file.
        """

        if queries is None:
            run_records = self.mocker_h.search_database(
                filter_criteria={
                    "collection" : "runs",
                    "table" : "provided_text"
                },
                perform_similarity_search = False,
                return_keys_list = ['run_id', 
                                    'query',
                                    'text',
                                    'timestamp']
        )

        else:
            run_records = self.mocker_h.search_database(
                filter_criteria={
                    "collection" : "runs",
                    "table" : "provided_text",
                    "query" : queries
                },
                perform_similarity_search = False,
                return_keys_list = ['run_id', 
                                    'query',
                                    'text',
                                    'timestamp'])

        run_ids = [run['run_id'] for run in run_records]

        scores = self.mocker_h.search_database(
            filter_criteria = {"collection" : "scores",
                                "table" : "runs",
                                "run_id" : run_ids},
                                perform_similarity_search = False)

        scores = [
            {k: v for k, v in d.items() if k not in ["collection",
                                                    "table"]}
            for d in scores
        ]

        if scores:
            run_records = self._merge_lists_by_key_full_left(
                 run_records, scores, "run_id")

            updated_list_of_dicts = [
                {**{'provided_text' if k == 'text' else k: v \
                    for k, v in dictionary.items()}}
                for dictionary in run_records
            ]

            
        elif run_records:

            updated_list_of_dicts = [
                {**{'provided_text' if k == 'text' else k: v \
                    for k, v in dictionary.items()}}
                for dictionary in run_records
            ]

        else:
            updated_list_of_dicts = [{
                'run_id' : None,
                'query' : None, 
                'expected_text' : None,
                'provided_text' : None,
                'timestamp' : None
            }]

        return updated_list_of_dicts

    def get_all_runs_df(self, queries = None):

        """
        Retrieves all runs as a DataFrame from the stored file.
        """

        df = pd.DataFrame(self.get_all_runs(queries=queries))
   
        return df.replace({np.nan: None})

    # def flush_records(self):

    #     """
    #     Clears all query records from the stored file, leaving only the headers.
    #     """

    #     # Open the file in write mode to clear it, then write back only the headers
    #     with open(self.record_file, mode='w', newline='', encoding='utf-8') as file:
    #         writer = csv.writer(file)
    #         writer.writerow(['id', 'timestamp', 'query', 'expected_text', 'tested', 'test_status'])  # column headers

    # def flush_comparison_results(self):

    #     """
    #     Deletes the file containing the comparison results.
    #     """

    #     # Check if the results file exists
    #     if os.path.isfile(self.results_file):
    #         os.remove(self.results_file)
    #     else:
    #         raise FileNotFoundError("No results file found. There's nothing to flush.")

    def compare_runs_with_records(self,                        
                            queries : list = None,
                            compare_scores : list = None,
                            ):

        """
        Compares the provided text with all recorded expected results for a specific query and stores the comparison results.
        """

        if compare_scores is None:
            compare_scores = self.compare_scores

        # pull relevant records
        records = self.get_all_records(queries=queries)

        # pull relevant runs
        runs = self.get_all_runs(queries=queries)

        records_runs = self._merge_lists_by_key_full_left(runs,records, "query")

        if not records_runs:
            raise ValueError("Query not found in records.")

        comparisons = []
        for record_run in records_runs:

            if record_run.get('run_id', None):

                comparison = {"collection" : "scores",
                              "table" : "runs",
                              "run_id": record_run['run_id']}

                comparison_scores = self.records_analyser.calculate_scores(
                    method_names = compare_scores, 
                    exp_text = record_run['expected_text'],
                    prov_text = record_run['provided_text'])
                
                comparison.update(comparison_scores)
                comparisons.append(comparison)

        if comparisons:

            self.mocker_h.insert_values(values_dict_list = comparisons,
                                        embed = False)
        else:
            self.logger.warning("No comparisons were completed for queries!")

    def calculate_aggr_scores(self,
                            queries : list = None,
                            aggr_scores : list = None,
                            ):

        """
        Calculate aggr scores for selected queries based on compare scores.
        """

        if aggr_scores is None:
            aggr_scores = self.aggr_scores

        # pull relevant runs
        df = self.get_all_runs_df(queries=queries)

        # get relevant queries
        queries = list(set(df['query']))
        
        comparisons = []
        for query in queries:
            
            # get score dataframe for each query
            df_scores = df.query(f"query == '{query}'").iloc[:,4:]

            comparison = {"collection" : "scores",
                              "table" : "records",
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

