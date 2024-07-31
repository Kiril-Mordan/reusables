import logging
import attrs #==23.2.0
import asyncio 
from typing import Any, AnyStr, Union, Optional, Sequence, Mapping, Literal, overload, Callable, Dict
import pandas as pd #==2.1.1
from mocker_db import MockerDB #==0.2.0


@attrs.define
class PromptHandler():

    """
    PromptHandler prepares inputs for the llm requests.
    """

    template : Optional[dict] = attrs.field(default=None)

    # Logger settings
    logger = attrs.field(default=None)
    logger_name = attrs.field(default='Prompt Handler Async')
    loggerLvl = attrs.field(default=logging.INFO)
    logger_format = attrs.field(default=None)

    def __attrs_post_init__(self):
        self._initialize_logger()

    def _initialize_logger(self):

        """
        Initialize a logger for the class instance based on the specified logging level and logger name.
        """

        if self.logger is None:
            logging.basicConfig(level=self.loggerLvl, format=self.logger_format)
            logger = logging.getLogger(self.logger_name)
            logger.setLevel(self.loggerLvl)

            self.logger = logger

    def apply_template(self, 
                       messages : list, 
                       template : dict = None):

        """
        Transforms messages according to prompt templates.
        """

        if template is None:
            template = self.template

        if template is None:
            return messages

        messages = messages.copy()

        return [{'role': message['role'],
                'content': template.get(message['role'], 
                "{content}").format(content=message['content'])}
            for message in messages
        ]

@attrs.define
class PromptStrategyHandler():

    """
    PromptStrategyHandler defines how to deal with single prompt call.
    """

    strategy_name : Optional[str] = attrs.field(default=None)
    strategy_params : Optional[dict] = attrs.field(default={})

    # Outputs
    responses : Optional[list] = attrs.field(default=[])
    last_responses : Optional[list] = attrs.field(default=[])

    # Logger settings
    logger = attrs.field(default=None)
    logger_name = attrs.field(default="Prompt Strategy Handler")
    loggerLvl = attrs.field(default=logging.INFO)
    logger_format = attrs.field(default=None)

    def __attrs_post_init__(self):
        self._initialize_logger()

    def _initialize_logger(self):

        """
        Initialize a logger for the class instance based on the specified logging level and logger name.
        """

        if self.logger is None:
            logging.basicConfig(level=self.loggerLvl, format=self.logger_format)
            logger = logging.getLogger(self.logger_name)
            logger.setLevel(self.loggerLvl)

            self.logger = logger

    async def _call_n_times(self, 
                            function: Callable, 
                            n_calls : int, 
                            *args, **kwargs):

        """
        Calls provided function n times.
        """

        response_calls = [function(*args, **kwargs) for _ in range(n_calls)]

        responses = await asyncio.gather(*response_calls)

        self.responses += responses
        self.last_responses = responses

        return responses

    
    async def most_common_output_of_3(self, 
                          function: Callable, 
                          strategy_params : dict, 
                          *args, **kwargs) -> Dict[str, Any]:

        """
        Calls function a given number of times and selects output
        of minimal length.
        """

        n_calls = 3

        responses = await self._call_n_times(
            function = function, 
            n_calls = n_calls, 
            *args, **kwargs)

        contents = [response['message']['content'] \
            for response in responses]

        
        # use mocker to find pair that is the closes according to cosine dist

        hh = MockerDB(
            embedder_params = {
                'model_name_or_path' : 'intfloat/multilingual-e5-base',
                'processing_type' : 'batch',
                'tbatch_size' : 500})

        hh.establish_connection()

        insert = [{
            'collection' : 'responses',
            'text' : text,
            'id' : rid} for text, rid in zip(contents, range(n_calls))]

        hh.insert_values(values_dict_list=insert,
                        var_for_embedding_name='text',
                        embed=True)

        records = []
        for text in contents:
            text2 = hh.search_database(query = text,
                                    filter_criteria={
                                        "collection" : "responses",
                                    },
                            return_keys_list=['text', 'id'],
                            search_results_n=2)

            #texts = [t['text'] for t in text2]

            records.append({
                'distance' : hh.results_dictances[1],
                'query' : text2[0]['text'],
                'id' : text2[0]['id']
            })

        # sorting ascending by distance (to pop later)
        rddf = pd.DataFrame(records).sort_values(
            by='distance',ascending=True)

        # extracting most_commonm_response_id
        most_commonm_response_id = rddf['id'].to_list().pop()

        return responses[most_commonm_response_id]


    async def min_output_length(self, 
                          function: Callable, 
                          strategy_params : dict, 
                          *args, **kwargs) -> Dict[str, Any]:

        """
        Calls function a given number of times and selects output
        of minimal length.
        """

        n_calls = max(strategy_params.get('n_calls', 2), 2)

        responses = await self._call_n_times(
            function = function, 
            n_calls = n_calls, 
            *args, **kwargs)

        contents = [response['message']['content'] \
            for response in responses]

        min_content = min(contents, key=len)

        # Find the response with the min content
        min_response = next(response for response in responses \
            if response['message']['content'] == min_content)
        return min_response

    async def max_output_length(self, 
                                function: Callable, 
                                strategy_params: dict, 
                                *args, **kwargs) -> Dict[str, Any]:
        """
        Calls function a given number of times and selects output of maximal length.
        """
        n_calls = max(strategy_params.get('n_calls', 2), 2)

        responses = await self._call_n_times(
            function=function, 
            n_calls=n_calls, 
            *args, **kwargs
        )

        contents = [response['message']['content'] for response in responses]
        max_content = max(contents, key=len)

        # Find the response with the max content
        max_response = next(response for response in responses if response['message']['content'] == max_content)
        return max_response

    async def last_call(self, 
                        function: Callable,
                        strategy_params: dict, 
                        *args, **kwargs) -> Dict[str, Any]:
        """
        Calls function a given number of times and selects output of maximal length.
        """
        n_calls = max(strategy_params.get('n_calls', 1), 1)

        responses = await self._call_n_times(
            function=function, 
            n_calls=n_calls, 
            *args, **kwargs
        )

        return responses[-1]

        
    async def call_async(self, 
             function: Callable, 
             strategy_name: Optional[str]= None, 
             strategy_params: Optional[dict] = None,
             *args, **kwargs) -> Any:

        """
        Calls a given function with selected strategy.
        """

        if strategy_name is None:
            strategy_name = self.strategy_name

        if strategy_params is None:
            strategy_params = self.strategy_params

        if strategy_name:

            strategy_name = getattr(self, strategy_name, None)
            if callable(strategy_name):
                return await strategy_name(
                    function = function, 
                    strategy_params=strategy_params,
                    *args, **kwargs)
            else:
                raise AttributeError(f"Strategy '{strategy_name}' not found")            
        else:
            return await function(*args, **kwargs)