import logging
import attr #>=22.2.0
import requests
import aiohttp
import asyncio
import ast

@attr.s
class LlmFilterConnector:

    connection_string = attr.ib(default = None)
    headers = attr.ib(default={
        "Content-Type": "application/json"
    })
    payload_extra = attr.ib(default={})

    system_message = attr.ib(
        default = """You are an advanced language model designed to search for specific content within a text snippet. Your task is to determine whether the provided text snippet contains information relevant to a given query. 
Your response should be strictly 'true' if the relevant information is present and 'false' if it is not. Do not provide any additional information or explanation. Here is how you should proceed:

1. Carefully read the provided text snippet.
2. Analyze the given query.
3. Determine if the text snippet contains information relevant to the query.
4. Respond only with 'true' or 'false' based on your determination.""")

    template = attr.ib(default = "Query: Does the text mention {query}? \nText Snippet: '''\n {text} \n'''")


    logger = attr.ib(default=None)
    logger_name = attr.ib(default='Llm Filter Connector')
    loggerLvl = attr.ib(default=logging.INFO)
    logger_format = attr.ib(default=None)

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

    def _make_inputs(self, query : str, inserts : list, search_key : str, system_message = None, template = None):

        if system_message is None:
            system_message = self.system_message

        if template is None:
            template = self.template

        return [[{'role' : 'system',
                'content' : system_message},
                {'role' : 'user',
                'content' : template.format(query = query, text = dd[search_key])}] for dd in inserts]

    def _call_sync_llm(self, 
                       messages : list,
                       payload_extra : dict):

        """
        Calls llm sync endpoint.
        """

        request_body = payload_extra
        request_body["messages"] = messages

        request_body_json = json.dumps(request_body)

        response = requests.post(self.connection_string,
                                 headers = self.headers,
                                 json=request_body_json)

        return response.json()

    async def _call_async_llm(self, 
                              payload_extra : dict, 
                              messages : list,
                              retry : int = 1):

        """
        Calls llm async endpoint.
        """

        request_body = payload_extra
        request_body["messages"] = messages

        request_body_json = json.dumps(request_body)

        retry += 1
        attempt = 0
        async with aiohttp.ClientSession() as session:
            while attempt < retry:
                try:
                    async with session.post(
                        url=self.connection_string,
                        headers=self.headers,
                        data=request_body_json) as request:

                        response = await request.json()

                    if request.status > 200:
                        raise Exception(f"Request failed: {request.status}")

                    retry = -1
                except Exception as e:
                    self.logger.error(e)
                    attempt += 1

        if attempt == retry:
            self.logger.error(f"Request failed after {attempt} attempts! {request_body_json}")
            response = {}

        return response

    def _filter_data(self, data : dict, responses : list):

        outputs = [res['message']['content'] for res in responses]

        output_filter = ['true' in out.lower() for out in outputs]

        filtered = {d : data[d] for d,b in zip(data,output_filter) if b}

        return filtered

    def filter_data(self,
                    query : str,
                    data : list,
                    search_key : str,
                    system_message : str = None,
                    template : str = None,
                    payload_extra : dict = None):

        """
        Prompts chat for search.
        """

        if payload_extra is None:
            payload_extra = self.payload_extra

        inserts = [value for _, value in data.items()]

        messages = self._make_inputs(query = query,
                                     inserts = inserts,
                                     search_key = search_key,
                                     system_message = system_message,
                                     template = template)

        responses = self._call_sync_llm(
            messages = messages,
            payload_extra = payload_extra)

        filtered = self._filter_data(data = data, responses = responses)

        return filtered

    async def filter_data_async(self,
                    query : str,
                    data : list,
                    search_key : str,
                    system_message : str = None,
                    template : str = None,
                    payload_extra : dict = None):

        """
        Prompts chat for search.
        """

        if self.connection_string:

            if payload_extra is None:
                payload_extra = self.payload_extra

            inserts = [value for _, value in data.items()]

            messages = self._make_inputs(query = query,
                                        inserts = inserts,
                                        search_key = search_key,
                                        system_message = system_message,
                                        template = template)

            requests = [self._call_async_llm(messages = message, 
                                            payload_extra = payload_extra) \
                                                for message in messages]

            responses = await asyncio.gather(*requests)

            filtered = self._filter_data(data = data, responses = responses)
        else:
            self.logger.warning("Provide connection_string in 'llm_filter_params' to use llm filters!")
            filtered = data

        return filtered