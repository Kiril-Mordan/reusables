from python_modules.mocker_db import MockerDB, SentenceTransformerEmbedder, MockerSimilaritySearch
import numpy as np



def test_initialization():

    # Test with default parameters
    default_handler = MockerDB(use_embedder = False)
    assert default_handler.file_path == "./mock_persist", "Default file path should be './mock_persist'"
    assert default_handler.persist is False, "Default persist should be False"

    # Test with custom parameters
    custom_handler = MockerDB(file_path="./custom_path", 
    persist=True,
    use_embedder = False)
    assert custom_handler.file_path == "./custom_path", "Custom file path should be './custom_path'"
    assert custom_handler.persist is True, "Custom persist should be True"


def test_embedding():
    handler = SentenceTransformerEmbedder(
        model_name_or_path = 'paraphrase-multilingual-mpnet-base-v2')
    test_sentence = "This is a test."
    embedding = handler.embed(test_sentence, processing_type='')
    print(embedding)
    assert embedding is not None, "Embedding should not be None"
    assert isinstance(embedding, np.ndarray), "Embedding should be a numpy array"

# def test_insertion():
#     handler = MockerDB()
#     handler.establish_connection()
#     test_data = [{"text": "Sample text"}]
#     handler.insert_values(test_data, "text")
#     assert "key1" in handler.data, "Data insertion failed"

def test_searching():
    handler = MockerDB(
        embedder_params = {'model_name_or_path' : 'paraphrase-multilingual-mpnet-base-v2',
                        'processing_type' : 'batch',
                        'tbatch_size' : 500}
    )
    handler.establish_connection()
    test_data = [{"text": "Sample text"}, {"text": "Another sample"}]
    handler.insert_values(test_data, "text")
    results = handler.search_database("Sample")
    assert len(results) > 0, "Search should return at least one result"

def test_searching_with_filtering():
    handler = MockerDB(
        embedder_params = {'model_name_or_path' : 'paraphrase-multilingual-mpnet-base-v2',
                        'processing_type' : 'batch',
                        'tbatch_size' : 500}
    )
    handler.establish_connection()
    test_data = [{"text": "Sample text"}, {"text": "Another sample"}]
    handler.insert_values(test_data, "text")
    results = handler.search_database("Sample",filter_criteria={'text' : 'Sample text'}, return_keys_list=['text'])
    assert results == [{"text": "Sample text"}]


def test_multiple_searching():
    handler = MockerDB(
        embedder_params = {'model_name_or_path' : 'paraphrase-multilingual-mpnet-base-v2',
                        'processing_type' : 'batch',
                        'tbatch_size' : 500}
    )
    handler.establish_connection()
    test_data = [{"text": "Sample text"}, {"text": "Another sample"}]
    handler.insert_values(test_data, "text")
    results_1 = handler.search_database("Sample",filter_criteria={'text' : 'Sample text'}, return_keys_list=['text'])
    results_2 = handler.search_database("Sample",filter_criteria={'text' : 'Another sample'}, return_keys_list=['text'])
    assert results_1 == [{"text": "Sample text"}]
    assert results_2 == [{"text": "Another sample"}]

# def test_filtering():
#     handler = MockerDB()
#     handler.establish_connection()
#     test_data = [{"category": "A"}, {"category": "B"}]
#     handler.insert_values(test_data, "category")
#     handler.filter_database({"category": "A"})
#     assert "key1" in handler.filtered_data, "Filtering failed"

# def test_deletion():
#     handler = MockerDB()
#     handler.establish_connection()
#     test_data = [{"text": "Sample text"}, {"text": "Another sample"}]
#     handler.insert_values(test_data, "text")
#     handler.remove_from_database({"text": "Sample text"})
#     assert "key1" not in handler.data, "Deletion failed"



