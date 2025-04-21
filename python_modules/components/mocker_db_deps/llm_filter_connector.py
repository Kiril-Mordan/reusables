import logging
import asyncio
import os
import ast
import json
import attrsx
import attrs #>=23.1.0
import requests
import aiohttp


@attrsx.define
class LlmFilterConnector:

    """
    Filters provided data using LLM connection
    """

    llm_h_class = attrs.field(default=None)
    llm_h = attrs.field(default=None)
    llm_h_params = attrs.field(default={})
    
    system_message = attrs.field(
        default = """You are an advanced language model designed to search for specific content within a text snippet. 
Your task is to determine whether the provided text snippet contains information relevant to a given query. 
Your response should be strictly 'true' if the relevant information is present and 'false' if it is not. 
Do not provide any additional information or explanation. Here is how you should proceed:

1. Carefully read the provided text snippet.
2. Analyze the given query.
3. Determine if the text snippet contains information relevant to the query.
4. Respond only with 'true' or 'false' based on your determination.""")

    template = attrs.field(default = "Query: Does the text mention {query}? \nText Snippet: '''\n {text} \n'''")

    max_retries = attrs.field(default=1)

    def __attrs_post_init__(self):
        self._initialize_llm_h()

    def _initialize_llm_h(self):

        if self.llm_h is None:
            self.llm_h = self.llm_h_class(**self.llm_h_params)

    def _make_inputs(self, query : str, inserts : list, search_key : str, system_message = None, template = None):

        if system_message is None:
            system_message = self.system_message

        if template is None:
            template = self.template

        return [[{'role' : 'system',
                'content' : system_message},
                {'role' : 'user',
                'content' : template.format(query = query, text = dd[search_key])}] for dd in inserts]


    async def _call_async_llm(self, 
                              messages : list):

        """
        Calls llm async endpoint.
        """

        retry = self.max_retries

        retry += 1
        attempt = 0

        while attempt < retry:
            try:
                
                response = await self.llm_h.chat(messages=messages)

                retry = -1
            except Exception as e:
                self.logger.error(e)
                attempt += 1

        if attempt == retry:
            self.logger.error(f"Request failed after {attempt} attempts!")
            response = {}

        return response

    def _filter_data(self, data : dict, responses : list):

        outputs = [res['choices'][0]['message']['content'] for res in responses]

        output_filter = ['true' in out.lower() for out in outputs]

        filtered = {d : data[d] for d,b in zip(data,output_filter) if b}

        return filtered

    async def filter_data_async(self,
                    search_specs : dict,
                    data : list,
                    system_message : str = None,
                    template : str = None):

        """
        Prompts chat for search.
        """

        try:
            inserts = [value for _, value in data.items()]

            all_messages = []
            for search_key, queries in search_specs.items():
                for query in queries:
                    messages = self._make_inputs(query = query,
                                                inserts = inserts,
                                                search_key = search_key,
                                                system_message = system_message,
                                                template = template)
                    all_messages.append(messages)

            all_requests = [self._call_async_llm(messages = messages) \
                for search_messages in all_messages for messages in search_messages]

            all_responses = await asyncio.gather(*all_requests)

            all_filtered = {}

            for m_id in range(len(all_messages)):

                responses = [all_responses[i] for i in range(m_id * len(data), (m_id + 1) * len(data))]

                filtered = self._filter_data(data = data, responses = responses)

                all_filtered.update(filtered)

        except Exception as e:
            self.logger.error(e)
            all_filtered = data

        return all_filtered
