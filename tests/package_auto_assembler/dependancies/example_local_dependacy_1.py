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
import attr #>=22.2.0



# Metadata for package creation
__package_metadata__ = {
    "author": "Kyrylo Mordan",
    "author_email": "parachute.repo@gmail.com",
    "version": "0.0.1",
    "description": "A mock handler for simulating a vector database.",
    "keywords" : ['python', 'vector database', 'similarity search']
    # Add other metadata as needed
}


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

