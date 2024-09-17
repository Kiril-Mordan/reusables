"""
Comparison Frame

Designed to automate and streamline the process of comparing textual data, particularly focusing on various metrics
such as character and word count, punctuation usage, and semantic similarity.
It's particularly useful for scenarios where consistent text analysis is required,
such as evaluating the performance of natural language processing models, monitoring content quality,
or tracking changes in textual data over time using manual evaluation.
"""

import string
import logging
import os
import csv
from collections import Counter
from datetime import datetime #==5.2
import dill #[test]==5.0.1
import pandas as pd #[all]==2.1.1
import attr #>=22.2.0
from sklearn.metrics.pairwise import cosine_similarity #==0.0.0
from sklearn.calibration import CalibratedClassifierCV, CalibrationDisplay #==1.3.1



@attr.s
class ComparisonFrame:

    """
    Compares query:response pairs expected vs recieved with semantic similarity
    and simple metrics of word count, line count etc.

    ...

    Attributes
    ----------
    embedder : SentenceTransformer
        The model used to generate embeddings for semantic comparison.
    record_file : str
        The name of the CSV file where queries and expected results are stored.
    results_file : str
        The name of the CSV file where comparison results are stored.
    embeddings_file : str
        The name of the file where embeddings are stored.
    margin_char_count_diff : int
        The acceptable margin for character count difference.
    margin_word_count_diff : int
        The acceptable margin for word count difference.
    margin_semantic_similarity : float
        The minimum acceptable semantic similarity.

    Methods
    -------
    record_query(query, expected_text, overwrite=True)
        Records a new query and its expected result in the record file.
    mark_query_as_tested(query, test_status)
        Marks a query as tested and updates its test status in the record file.
    save_embeddings(query, expected_text)
        Saves the embeddings for the expected text of a query.
    load_embeddings(query)
        Loads the saved embeddings for a query.
    get_all_queries(untested_only=False)
        Retrieves all queries or only untested ones from the record file.
    get_comparison_results()
        Retrieves the comparison results as a DataFrame.
    get_all_records()
        Retrieves all records from the record file.
    flush_records()
        Clears all records from the record file.
    flush_comparison_results()
        Deletes the comparison results file.
    compare_with_record(query, provided_text, mark_as_tested=True)
        Compares a provided text with the recorded expected result of a query.
    compare(exp_text, prov_text, query='')
        Compares two texts and returns the comparison metrics.
    compare_char_count(exp_text, prov_text)
        Computes the difference in character count between two texts.
    compare_word_count(exp_text, prov_text)
        Computes the difference in word count between two texts.
    compare_line_count(exp_text, prov_text)
        Computes the difference in line count between two texts.
    compare_punctuation(exp_text, prov_text)
        Computes the difference in punctuation usage between two texts.
    compare_semantic_similarity(exp_text, prov_text)
        Computes the semantic similarity between two texts.
    reset_record_statuses(record_ids=None)
        Resets the 'tested' status of specific queries or all queries in the record file, making them available for re-testing. Accepts an optional list of record IDs to reset; otherwise, resets all records.
    """

    embedder = attr.ib(default=None)
    model_name = attr.ib(default='all-mpnet-base-v2')

    # Files saved to persist
    record_file = attr.ib(default="record_file.csv")  # file where queries and expected results are stored
    results_file = attr.ib(default="comparison_results.csv") # file where comparison results will be stored
    embeddings_file = attr.ib(default="embeddings.dill")

    # Define acceptable margins
    margin_char_count_diff = attr.ib(default=10)
    margin_word_count_diff = attr.ib(default=5)
    margin_semantic_similarity = attr.ib(default=0.95)

    # Logger settings
    logger = attr.ib(default=None)
    logger_name = attr.ib(default='ComparisonFrame')
    loggerLvl = attr.ib(default=logging.INFO)

    def __attrs_post_init__(self):
        self.initialize_logger()
        self.initialize_record_file()
        self.initialize_embedder()


    def initialize_logger(self):

        """
        Initialize a logger for the class instance based on
        the specified logging level and logger name.
        """

        if self.logger is None:
            logging.basicConfig(level=self.loggerLvl)
            logger = logging.getLogger(self.logger_name)
            logger.setLevel(self.loggerLvl)

            self.logger = logger

    def initialize_record_file(self):

        """
        Initialize empty records file and saves it locally
        if it was not found in specified location.
        """

        # Create a new file with headers if it doesn't exist
        if not os.path.isfile(self.record_file):
            with open(self.record_file, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                # Include 'test_status' in the headers from the beginning
                writer.writerow(['id', 'timestamp', 'query', 'expected_text', 'tested', 'test_status'])  # Added 'test_status'


    def initialize_embedder(self, model_name : str = None, reset : bool = True):

        """
        Initialize embedder for the class instance for a chosen model from sentence_transformer.
        """

        if model_name is None:
            model_name = self.model_name

        if (self.embedder is None) or reset:

            if model_name:
                try:
                    self.embedder = SentenceTransformer(model_name)
                    self.model_name = model_name
                except Exception as e:
                    self.logger.error("Provided model name was not loaded!")
                    print(e)

            else:
                self.logger.error("Model name is missing!")
                self.logger.error("Either provide 'embedder' parameter or 'model_name' parameter!")
                raise ValueError("Missing 'model_name' parameter!")
        else:

            # check if embedder is from sentence transformer
            if not isinstance(embedder, SentenceTransformer):
                self.logger.warning("Provided embedder should be from sentence_transformer package!")
                raise TypeError("embedder is not an instance of SentenceTransformer")


    def record_query(self, query, expected_text, overwrite=True):

        """
        Records a new query and its expected result in the record file.
        """

        rows = []
        max_id = 0
        # Read the existing data
        if os.path.isfile(self.record_file):
            with open(self.record_file, mode='r', encoding='utf-8') as file:
                reader = csv.reader(file)
                rows = list(reader)
                if len(rows) > 1:  # if there's more than just the header
                    # find the maximum id (which is in the first column and convert it to int)
                    max_id = max(int(row[0]) for row in rows[1:])

        new_id = max_id + 1
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # current time in string format

        # If overwrite is True, update the existing record if the query exists; otherwise, append the new record
        if overwrite:
            for index, row in enumerate(rows):
                if len(row) > 2 and row[2] == query:  # queries are in the third column
                    rows[index] = [str(new_id), current_time, query, expected_text, 'no', '']  # 'no' indicates untested, '' for empty test_status
                    break
            else:
                rows.append([str(new_id), current_time, query, expected_text, 'no', ''])  # 'no' indicates untested, '' for empty test_status
        else:
            rows.append([str(new_id), current_time, query, expected_text, 'no', ''])  # 'no' indicates untested, '' for empty test_status

        self.save_embeddings(query=query,
                             expected_text=expected_text)

        # Write the updated data back to the file
        with open(self.record_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerows(rows)

    def mark_query_as_tested(self, query, test_status):
        """
        Updates the 'tested' status and 'test_status' of a specific query in the record file.
        """

        # Read the existing data
        rows = []
        with open(self.record_file, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            rows = list(reader)

        headers = rows[0]  # Extract the headers
        # Check if 'test_status' is in headers, if not, add it
        if 'test_status' not in headers:
            headers.append('test_status')

        # Find the query and mark it as tested, and update the test status
        for row in rows[1:]:  # Skip the header row
            if row[2] == query:  # if the query matches
                row[4] = 'yes'  # 'yes' indicates tested
                if len(row) >= 6:  # if 'test_status' column exists
                    row[5] = test_status  # update the 'test_status' column
                else:
                    row.append(test_status)  # if 'test_status' column doesn't exist, append the status

        # Write the updated data back to the file, including the headers
        with open(self.record_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(headers)  # Write the headers first
            writer.writerows(rows[1:])  # Write the data rows


    def reset_record_statuses(self, record_ids=None):
        """
        Resets the 'tested' status of specific queries or all queries in the record file, making them available for re-testing.

        Parameters:
        record_ids (list of int): Optional. A list of record IDs for which to reset the statuses. If None, all records are reset.
        """

        # Read the existing data
        with open(self.record_file, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            rows = list(reader)

        # Check for the right headers and adjust the data rows
        headers = rows[0]  # Extract the headers
        if 'test_status' not in headers:
            headers.append('test_status')  # Add 'test_status' to headers if it's missing

        new_rows = [headers]  # Include the headers as the first row

        for row in rows[1:]:  # Skip the header row
            if record_ids is None or int(row[0]) in record_ids:  # Check if resetting all or specific IDs
                new_row = row[:5]  # Select columns 'id' through 'tested'
                new_row[4] = 'no'  # 'no' indicates untested
                if len(row) == 6:  # if 'test_status' column exists
                    new_row.append('')  # reset 'test_status' to an empty string
                else:
                    new_row.append('')  # if 'test_status' column doesn't exist, still add an empty string placeholder
                new_rows.append(new_row)
            else:
                new_rows.append(row)  # If the ID is not in the list, keep the row unchanged

        # Write the updated data back to the file, including the headers
        with open(self.record_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerows(new_rows)  # Write the updated rows back to CSV, including headers

    def save_embeddings(self, query, expected_text):

        """
        Generates and stores the embeddings for the expected text of a specific query.
        """

        # Generate embeddings
        embeddings = self.embedder.encode(expected_text)

        # Load existing data or create new
        if os.path.exists(self.embeddings_file):
            with open(self.embeddings_file, 'rb') as file:
                data = dill.load(file)
        else:
            data = {}

        # Add new embeddings
        data[query] = embeddings

        # Save data

        embeddings_with_model_name = {'model_name' : self.model_name,
                                      'embeddings' : data}

        with open(self.embeddings_file, 'wb') as file:
            dill.dump(embeddings_with_model_name, file)

    def load_embeddings(self, query):

        """
        Retrieves the stored embeddings for a specific query.
        """

        # Check if embeddings file exists
        if not os.path.exists(self.embeddings_file):
            raise FileNotFoundError("No embeddings file found. Please generate embeddings first.")

        # Load data
        with open(self.embeddings_file, 'rb') as file:
            embeddings_with_model_name = dill.load(file)

        self.logger.debug(f"Model name for the loaded embeddings: {embeddings_with_model_name['model_name']}")

        # Retrieve embeddings for the given query
        embeddings = embeddings_with_model_name['embeddings'].get(query)

        if embeddings is None:
            raise ValueError(f"No embeddings found for query: {query}")

        return embeddings


    def get_all_queries(self, untested_only=False):

        """
        Retrieves a list of all recorded queries, with an option to return only those that haven't been tested.
        """

        # Read the recorded data and retrieve all queries
        queries = []
        with open(self.record_file, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)  # skip headers
            if untested_only:
                queries = [row[2] for row in reader if row[4] == 'no']  # select only untested queries
            else:
                queries = [row[2] for row in reader]  # select all queries

        return queries

    def get_comparison_results(self, throw_error : bool = False):

        """
        Retrieves the comparison results as a DataFrame from the stored file.
        """

        # Check if the results file exists
        if not os.path.isfile(self.results_file):
            error_mess = "No results file found. Please perform some comparisons first."
            if throw_error:
                raise FileNotFoundError(error_mess)
            else:
                self.logger.error(error_mess)

        else:
            # Read the CSV file into a pandas DataFrame
            df = pd.read_csv(self.results_file)

            return df

    def get_all_records(self):

        """
        Retrieves all query records as a DataFrame from the stored file.
        """

        # Check if the record file exists
        if not os.path.isfile(self.record_file):
            raise FileNotFoundError("No record file found. Please record some queries first.")

        # Read the CSV file into a pandas DataFrame
        df = pd.read_csv(self.record_file)

        return df

    def flush_records(self):

        """
        Clears all query records from the stored file, leaving only the headers.
        """

        # Open the file in write mode to clear it, then write back only the headers
        with open(self.record_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['id', 'timestamp', 'query', 'expected_text', 'tested', 'test_status'])  # column headers

    def flush_comparison_results(self):

        """
        Deletes the file containing the comparison results.
        """

        # Check if the results file exists
        if os.path.isfile(self.results_file):
            os.remove(self.results_file)
        else:
            raise FileNotFoundError("No results file found. There's nothing to flush.")

    def compare_with_record(self,
                            query : str,
                            provided_text : str,
                            mark_as_tested : bool = True,
                            return_results : bool = False):

        """
        Compares the provided text with all recorded expected results for a specific query and stores the comparison results.
        """

        # Read the recorded data and find all records for the query, sorted by timestamp
        with open(self.record_file, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            # Skip the header, find all rows with the matching query, and sort them by the timestamp
            records = sorted(
                (row for row in reader if len(row) > 2 and row[2] == query),
                key=lambda x: x[1],
                reverse=True  # most recent first
            )

        if not records:
            raise ValueError("Query not found in records.")

        comparisons = []
        for record in records:
            expected_text = record[3]  # expected text is in the fourth column
            comparison = self.compare(expected_text, provided_text, query=query)
            comparison['id'] = record[0]  # id is in the first column
            comparisons.append(comparison)


        # After conducting the comparison
        for comparison in comparisons:
            # Check if differences are within acceptable margins
            passed_char_count = comparison['char_count_diff'] <= self.margin_char_count_diff
            passed_word_count = comparison['word_count_diff'] <= self.margin_word_count_diff
            passed_semantic_similarity = comparison['semantic_similarity'] >= self.margin_semantic_similarity

            # If all checks pass, mark as 'pass'; otherwise, 'fail'
            if passed_char_count and passed_word_count and passed_semantic_similarity:
                test_status = 'pass'
            else:
                test_status = 'fail'

            # If required, mark the query as tested with the test status
            if mark_as_tested:
                self.mark_query_as_tested(query, test_status)

        # Convert results list to DataFrame
        results_df = pd.DataFrame(comparisons)

        # Save results DataFrame to CSV
        # 'mode='a'' will append the results to the existing file;
        # 'header=not os.path.isfile(self.results_file)' will write headers only if the file doesn't already exist
        results_df.to_csv(self.results_file, mode='a', header=not os.path.isfile(self.results_file), index=False)

        if return_results:
            return results_df

    def compare(self, exp_text : str, prov_text : str, query : str = ''):

        """
        Performs a detailed comparison between two texts, providing metrics like character count, word count, semantic similarity, etc.
        """

        results = {
            'query' : query,
            'char_count_diff': self.compare_char_count(exp_text, prov_text),
            'word_count_diff': self.compare_word_count(exp_text, prov_text),
            'line_count_diff': self.compare_line_count(exp_text, prov_text),
            'punctuation_diff': self.compare_punctuation(exp_text, prov_text),
            'semantic_similarity': self.compare_semantic_similarity(exp_text, prov_text),
            'expected_text' : exp_text,
            'provided_text' : prov_text
        }

        return results

    def compare_char_count(self, exp_text, prov_text):

        """
        Calculates the absolute difference in the number of characters between two texts.
        """

        return abs(len(exp_text) - len(prov_text))

    def compare_word_count(self, exp_text, prov_text):

        """
        Calculates the absolute difference in the number of words between two texts.
        """

        return abs(len(exp_text.split()) - len(prov_text.split()))

    def compare_line_count(self, exp_text, prov_text):

        """
        Calculates the absolute difference in the number of lines between two texts.
        """

        return abs(len(exp_text.splitlines()) - len(prov_text.splitlines()))

    def compare_punctuation(self, exp_text, prov_text):

        """
        Calculates the total difference in the use of punctuation characters between two texts.
        """

        punctuation1 = Counter(char for char in exp_text if char in string.punctuation)
        punctuation2 = Counter(char for char in prov_text if char in string.punctuation)
        return sum((punctuation1 - punctuation2).values()) + sum((punctuation2 - punctuation1).values())


    def compare_semantic_similarity(self, exp_text, prov_text):

        """
        Computes the semantic similarity between two pieces of text using their embeddings.
        """

        embedding1 = self.embedder.encode(exp_text).reshape(1, -1)
        embedding2 = self.embedder.encode(prov_text).reshape(1, -1)
        return cosine_similarity(embedding1, embedding2)[0][0]