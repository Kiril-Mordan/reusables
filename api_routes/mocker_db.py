
import numpy as np
import os
import yaml

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from mocker_db.mocker_db import *

router = APIRouter(prefix = "/mocker-db")

MOCKER_SETUP_PARAMS = {
    'embedder_params' :
  {'model_name_or_path' : 'intfloat/multilingual-e5-base',
  'processing_type' : 'batch',
  'tbatch_size' : 500},
    'similarity_params' : {'space':'cosine'},
    'file_path' : "./persist/",
    'embs_file_path' : "./persist/",
    'persist' : True
}

API_SETUP_PARAMS = {
    'memory_scaler_from_bytes': 1048576,
    'allocated_mb': 8192,
    'use_env_vars': True
}

config = ".mockerdb.api.config"
if os.getenv("MOCKER_API_CONFIG") and os.path.exists(os.getenv("MOCKER_API_CONFIG")):
    config = os.getenv("MOCKER_API_CONFIG")

if os.path.exists(config):
    with open(config, 'r') as file:
        api_config_up = yaml.safe_load(file)

    MOCKER_SETUP_PARAMS.update(
        api_config_up.get('MOCKER_SETUP_PARAMS', {}))

    API_SETUP_PARAMS.update(
        api_config_up.get('API_SETUP_PARAMS', {}))

if API_SETUP_PARAMS.get('use_env_vars'):

    if os.getenv("MOCKER_PERSIST_PATH"):
        MOCKER_SETUP_PARAMS['file_path'] = os.getenv("MOCKER_PERSIST_PATH")
        MOCKER_SETUP_PARAMS['embs_file_path'] = os.getenv("MOCKER_PERSIST_PATH")
    if os.getenv("MOCKER_ALLOCATED_MB"):
        API_SETUP_PARAMS['allocated_mb'] = os.getenv("MOCKER_ALLOCATED_MB")


handlers = {}
handlers['default'] = MockerDB(**{**MOCKER_SETUP_PARAMS, 
'file_path' : os.path.join(MOCKER_SETUP_PARAMS['file_path'], "mock_persist"),
'embs_file_path' : os.path.join(MOCKER_SETUP_PARAMS['embs_file_path'],"mock_embs_persist")})
handlers['default'].establish_connection()

@router.get("/")
async def read_root():
    return "Still alive!"

@router.get("/active_handlers",
         description= "Displays the current active handlers, the number of items they manage, and their memory usage in megabytes.",
         responses = ActivateHandlersDesc)
def show_handlers():

    try:

        handler_names = [hn for hn in handlers]
        items_in_handlers = [len(handlers[hn].data.keys()) for hn in handlers]
        memory_usages = [obj_size(handlers[hn])/API_SETUP_PARAMS['memory_scaler_from_bytes'] \
            for hn in handlers]

        out = [{'handler': handler_name,
            'items': items_in_handler,
            'memory_usage': memory_usage} \
                for handler_name, items_in_handler, memory_usage \
                    in zip(handler_names, items_in_handlers, memory_usages) ]

        status = 'success'
        message = ''
    except Exception as e:
        status = 'failure'
        message = f'{e}'


    return {
        'results' : out,
        'status' : status,
        'message' : message,
        'handlers': handler_names,
        'items': items_in_handlers,
        'memory_usage': memory_usages
    }

@router.post("/remove_handlers",
          description = "Removes specified handlers from the application.",
          responses = RemoveHandlersDesc)
def remove_handlers(request: RemoveHandlersRequest):

    try:
        removed_handlers = []
        not_found_handlers = []

        for handler_name in request.handler_names:
            if handler_name in handlers:
                # Remove the handler
                del handlers[handler_name]
                removed_handlers.append(handler_name)
            else:
                not_found_handlers.append(handler_name)

        # Force garbage collection
        gc.collect()

        status = 'success'
        message = f"Removed handlers: {', '.join(removed_handlers)}"

        if not removed_handlers and not_found_handlers:
            status = 'failure'
            message=f"Handlers not found: {', '.join(not_found_handlers)}"

        
    except Exception as e:
        status = 'failure'
        message = f"{e}"


    return {
        "status" : status,
        "message": message,
        "not_found": not_found_handlers}

@router.post("/initialize",
          description = "Initializes the database with custom parameters.",
          responses = InitializeDesc)
def initialize_database(params: InitializeParams):
    global handlers  # Use global to modify the handler instance
    try:
        # Update the initialization parameters based on input
        init_params = MOCKER_SETUP_PARAMS.copy()  # Start with default setup parameters
        if params.embedder_params is not None:
            init_params["embedder_params"] = params.embedder_params
        if params.database_name is not None:
            init_params["file_path"] = os.path.join(extract_directory(MOCKER_SETUP_PARAMS["file_path"]),
                                                    f"mocker_{params.database_name}")  # Assuming the file path format
            init_params["embs_file_path"] = os.path.join(extract_directory(MOCKER_SETUP_PARAMS["embs_file_path"]),
                                                        f"embs_{params.database_name}")
        # Reinitialize the handler with new parameters
        handlers[params.database_name] = MockerDB(**init_params)
        handlers[params.database_name].establish_connection()

        status = 'success'
        message = ''
    except Exception as e:
        status = 'failure'
        message = f"{e}"
    return {
        "status" : status,
        "message": message}

@router.post("/insert",
          description = "Inserts data into the specified database.",
          responses = InsertDesc)
def insert_data(insert_request: InsertItem):

    try:
        # Extract values from the request object
        values_list = insert_request.data
        var_for_embedding_name = insert_request.var_for_embedding_name
        embed = insert_request.embed

        if insert_request.database_name is None:
            insert_request.database_name = "default"

        #Free up memory if needed
        check_and_offload_handlers(handlers = handlers,
                                allocated_bytes = API_SETUP_PARAMS['allocated_mb']*1024**2,
                                exception_handlers = [insert_request.database_name],
                                insert_size_bytes = obj_size(values_list))
        
        # Call the insert_values method with the provided parameters
        handlers[insert_request.database_name].insert_values(values_list, var_for_embedding_name, embed)
        
        status = 'success'
        message = ''
    except Exception as e:
        status = 'failure'
        message = f'{e}'
    
    return {
        "status": status,
        "message": message}

@router.post("/search",
          description = "Searches the database based on the provided query and criteria.",
          responses = SearchDesc)
async def search_data(search_request: SearchRequest):

    if search_request.database_name is None:
        search_request.database_name = "default"

    
    if search_request.database_name in handlers.keys():

        try:

            results = await handlers[search_request.database_name].search_database_async(
                query=search_request.query,
                search_results_n=search_request.search_results_n,
                llm_search_keys=search_request.llm_search_keys,
                keyword_check_keys=search_request.keyword_check_keys,
                keyword_check_cutoff=search_request.keyword_check_cutoff,
                filter_criteria=search_request.filter_criteria,
                similarity_search_type=search_request.similarity_search_type,
                similarity_params=search_request.similarity_params,
                perform_similarity_search=search_request.perform_similarity_search,
                return_keys_list=search_request.return_keys_list
            )

            # Ensure all numpy arrays are converted to lists
            json_compatible_results = []
            for result in results:
                processed_result = {}
                for key, value in result.items():
                    if isinstance(value, np.ndarray):
                        processed_result[key] = value.tolist()  # Convert numpy arrays to lists
                    elif isinstance(value, np.float32):
                        processed_result[key] = value.item()
                    else:
                        processed_result[key] = value
                json_compatible_results.append(processed_result)

            status = 'success'
            message = ''
        except Exception as e:
            status = 'failure'
            message = f'{e}'
    else:
        status = 'failure'
        message = 'handler not initialized'
        json_compatible_results = []
        

    return {
        "status" : status,
        "message" : message,
        "handler" : search_request.database_name,
        "results": json_compatible_results}

@router.post("/delete",
          description = "Deletes data from the database based on filter criteria.",
          responses = DeleteDesc)
def delete_data(delete_request: DeleteItem):

    if delete_request.database_name is None:
        delete_request.database_name = "default"

    filter_criteria = delete_request.filter_criteria

    try:
        if filter_criteria is None:
            handlers[delete_request.database_name].flush_database()
        else:
            handlers[delete_request.database_name].remove_from_database(filter_criteria)
        status = "success"
        message = ''
    except Exception as e:
        status = 'failure'
        message = f'{e}'
        
    return {
        "status": status,
        "message" : message}

@router.post("/embed",
          description = "Generates embeddings for the provided list of texts.",
          responses = EmbedDesc)
def embed_texts(embedding_request: EmbeddingRequest):

    try:
        init_params = MOCKER_SETUP_PARAMS.copy()  # Start with default setup parameters
        # update model
        if embedding_request.embedding_model is not None:
            init_params["embedder_params"]['model_name_or_path'] = embedding_request.embedding_model
        # switch cache location
        init_params["file_path"] = os.path.join(extract_directory(MOCKER_SETUP_PARAMS["file_path"]),
                                                f"cache_mocker_{init_params['embedder_params']['model_name_or_path'].replace('/','_')}")
        init_params["embs_file_path"] = os.path.join(extract_directory(MOCKER_SETUP_PARAMS["embs_file_path"]),
                                                    f"cache_embs_{init_params['embedder_params']['model_name_or_path'].replace('/','_')}")

        # create insert list of dicts
        insert = [{'text' : text} for text in embedding_request.texts]


        # Reinitialize the handler with new parameters
        cache_name = f"cache_mocker_{init_params['embedder_params']['model_name_or_path'].replace('/','_')}"

    
        # Free up memory if needed
        check_and_offload_handlers(handlers = handlers,
                                allocated_bytes = API_SETUP_PARAMS['allocated_mb']*1024**2,
                                exception_handlers = [cache_name],
                                insert_size_bytes = obj_size(insert))

        if cache_name not in [hn for hn in handlers]:

            handlers[cache_name] = MockerDB(**init_params)
            handlers[cache_name].establish_connection()

        # Use the embedder instance to get embeddings for the list of texts
        handlers[cache_name].insert_values(values_dict_list=insert,
                                            var_for_embedding_name='text',
                                            embed=True)

        # Retrieve list of embeddings
        embeddings = [handlers[cache_name].search_database(query = query,
                                            return_keys_list=['embedding'],
                                            search_results_n=1)[0]['embedding'].tolist() \
            for query in embedding_request.texts]

        status = 'success'
        message = ''
    except Exception as e:
        status = 'failure'
        message = f"{e}"
        cache_name = ''
        embeddings = []

    return JSONResponse(content={
        "status" : status,
        "message" : message,
        "handler" : cache_name,
        "embedding_model" : embedding_request.embedding_model,
        "embeddings": embeddings})
