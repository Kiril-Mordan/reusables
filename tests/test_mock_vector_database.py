from python_modules.mock_vector_database import MockVecDbHandler
import numpy as np

def test_initialization():
    # Test with default parameters
    default_handler = MockVecDbHandler()
    assert default_handler.file_path == "../redis_mock", "Default file path should be '../redis_mock'"
    assert default_handler.persist is False, "Default persist should be False"

    # Test with custom parameters
    custom_handler = MockVecDbHandler(file_path="./custom_path", persist=True)
    assert custom_handler.file_path == "./custom_path", "Custom file path should be './custom_path'"
    assert custom_handler.persist is True, "Custom persist should be True"


def test_embedding():
    handler = MockVecDbHandler()
    test_sentence = "This is a test."
    embedding = handler.embed(test_sentence)
    assert embedding is not None, "Embedding should not be None"
    assert isinstance(embedding, np.ndarray), "Embedding should be a numpy array"

def test_insertion():
    handler = MockVecDbHandler()
    handler.establish_connection()
    test_data = {"key1": {"text": "Sample text"}}
    handler.insert_values_dict(test_data, "text")
    assert "key1" in handler.data, "Data insertion failed"

def test_searching():
    handler = MockVecDbHandler()
    handler.establish_connection()
    test_data = {"key1": {"text": "Sample text"}, "key2": {"text": "Another sample"}}
    handler.insert_values_dict(test_data, "text")
    results = handler.search_database("Sample")
    assert len(results) > 0, "Search should return at least one result"

def test_searching_with_filtering():
    handler = MockVecDbHandler()
    handler.establish_connection()
    test_data = {"key1": {"text": "Sample text"}, "key2": {"text": "Another sample"}}
    handler.insert_values_dict(test_data, "text")
    results = handler.search_database("Sample",filter_criteria={'text' : 'Sample text'}, return_keys_list=['text'])
    assert results == [{"text": "Sample text"}]


def test_multiple_searching():
    handler = MockVecDbHandler()
    handler.establish_connection()
    test_data = {"key1": {"text": "Sample text"}, "key2": {"text": "Another sample"}}
    handler.insert_values_dict(test_data, "text")
    results_1 = handler.search_database("Sample",filter_criteria={'text' : 'Sample text'}, return_keys_list=['text'])
    results_2 = handler.search_database("Sample",filter_criteria={'text' : 'Another sample'}, return_keys_list=['text'])
    assert results_1 == [{"text": "Sample text"}]
    assert results_2 == [{"text": "Another sample"}]

def test_filtering():
    handler = MockVecDbHandler()
    handler.establish_connection()
    test_data = {"key1": {"category": "A"}, "key2": {"category": "B"}}
    handler.insert_values_dict(test_data, "category")
    handler.filter_database({"category": "A"})
    assert "key1" in handler.filtered_data, "Filtering failed"

def test_deletion():
    handler = MockVecDbHandler()
    handler.establish_connection()
    test_data = {"key1": {"text": "Sample text"}, "key2": {"text": "Another sample"}}
    handler.insert_values_dict(test_data, "text")
    handler.remove_from_database({"text": "Sample text"})
    assert "key1" not in handler.data, "Deletion failed"



