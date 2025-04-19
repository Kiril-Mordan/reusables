import logging
import attrsx
import attrs #>=23.1.0
import httpx

@attrsx.define
class MockerConnector:

    """
    Client for connecting to MockerDB api.
    """

    connection_details = attrs.field(
        default = {
            "base_url" : "http://localhost:8000"
        })

    client = attrs.field(default = None)

    def __attrs_post_init__(self):
        self.client = httpx.Client(
            **self.connection_details)

    def read_root(self):
        response = self.client.get("/")
        return response.text

    def show_handlers(self):

        """
        Show active handlers
        """

        response = self.client.get("/active_handlers")
        return response.json()

    
    def initialize_database(self,
                            database_name : str = 'default',
                            embedder_params : dict = None):

        """
        Initialize database handler.
        """

        params = {}

        if database_name is not None:
            params["database_name"] = database_name

        if embedder_params is not None:
            params["embedder_params"] = embedder_params

        response = self.client.post("/initialize", json=params)
        return response.json()

    def remove_handlers(self,
                        handler_names : list):

        """
        Remove active handlers
        """

        response = self.client.post("/remove_handlers", json={"handler_names": handler_names})
        if response.status_code == 404:
            raise Exception(response.json()['detail'])
        return response.json()

    def insert_data(self,
                    data : list,
                    database_name : str = 'default',
                    var_for_embedding_name : str = None,
                    embed=False):

        """
        Insert data into a select handler.
        """

        request_body = {"data": data,
                        "var_for_embedding_name" : "text"}

        if var_for_embedding_name is not None:
            request_body["var_for_embedding_name"] = var_for_embedding_name
        if database_name is not None:
            request_body["database_name"] = database_name
        if embed is not None:
            request_body["embed"] = embed

        response = self.client.post("/insert", json=request_body)
        return response.json()

    def search_data(self,
                    database_name : str = 'default',
                    query : str = None,
                    filter_criteria : dict = None,
                    llm_search_keys: list = None,
                    keyword_check_keys : list = None,
                    keyword_check_cutoff : float = None,
                    return_keys_list : list = None,
                    search_results_n : int = None,
                    similarity_search_type : str = None,
                    similarity_params : dict = None,
                    perform_similarity_search : bool = None):

        """
        Search data in selected handler.
        """

        request_body = {"database_name" : database_name}

        if query is not None:
            request_body["query"] = query
        if filter_criteria is not None:
            request_body["filter_criteria"] = filter_criteria
        if llm_search_keys is not None:
            request_body["llm_search_keys"] = llm_search_keys
        if keyword_check_keys is not None:
            request_body["keyword_check_keys"] = keyword_check_keys
        if keyword_check_cutoff is not None:
            request_body["keyword_check_cutoff"] = keyword_check_cutoff
        if return_keys_list is not None:
            request_body["return_keys_list"] = return_keys_list
        if search_results_n is not None:
            request_body["search_results_n"] = search_results_n
        if similarity_search_type is not None:
            request_body["similarity_search_type"] = similarity_search_type
        if similarity_params is not None:
            request_body["similarity_params"] = similarity_params
        if perform_similarity_search is not None:
            request_body["perform_similarity_search"] = perform_similarity_search

        response = self.client.post("/search", json=request_body)
        return response.json()

    def delete_data(self,
                    database_name : str,
                    filter_criteria : dict = None):

        """
        Delete data from selected handler
        """

        request_body = {"database_name": database_name}

        if filter_criteria is not None:
            request_body["filter_criteria"] = filter_criteria

        response = self.client.post("/delete", json=request_body)
        return response.json()

    def embed_texts(self,
                    texts : list,
                    embedding_model : str = None):

        """
        Embed list of text
        """

        request_body = {"texts": texts}

        if embedding_model is not None:
            request_body["embedding_model"] = embedding_model

        response = self.client.post("/embed", json=request_body)
        return response.json()
