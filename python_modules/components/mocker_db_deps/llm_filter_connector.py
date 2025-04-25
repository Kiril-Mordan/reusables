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

        messages = [[{'role' : 'system',
                'content' : system_message},
                {'role' : 'user',
                'content' : template.format(query = query, text = dd[search_key])}] for dd in inserts]

        texts = [dd[search_key] for dd in inserts]

        return messages, texts


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

    def _add_cats_to_filtered(self, data_item : dict, cats : dict):

        di = data_item

        cats_key = list(cats.keys())[0]
        
        if cats_key not in di.keys():
            di[cats_key] = []

        di[cats_key].append(cats[cats_key])

        return di

    def _extract_class_from_llm_output(self, responses : list):

        outputs = [res['choices'][0]['message']['content'] for res in responses]

        output_filter = ['true' in out.lower() for out in outputs]

        return output_filter


    def _filter_data(self, data : dict, output_filter : list, cats : dict):


        filtered = {d : {**data[d], "&cats" : self._add_cats_to_filtered(
            data_item = data[d].get("&cats",{}), cats=cats
        )  } \
            for d,b in zip(data,output_filter) if b}

        return filtered

    def _update_all_cats_cache(self,
                    all_cats_cache : dict,
                    output_filter : list, 
                    texts : dict):

        category = list(texts.keys())[0]

        for text, add_cat in zip(texts[category], output_filter):


            if text not in all_cats_cache.keys():
                all_cats_cache[text] = {1 : [], 0 : []}

            if add_cat:
                all_cats_cache[text][1].append(category)
            else:
                all_cats_cache[text][0].append(category)

        return all_cats_cache


    async def filter_data_async(self,
                    search_specs : dict,
                    data : list,
                    cats_cache : dict,
                    system_message : str = None,
                    template : str = None):

        """
        Prompts chat for search.
        """

        try:
            inserts = [value for _, value in data.items()]
            data_keys = [key for key, _ in data.items()]

            previously_classified = {}
            all_messages = []
            all_cats_filtered = []
            all_texts = []
        
            for search_key, queries in search_specs.items():
                for query in queries:
                    messages, texts = self._make_inputs(query = query,
                                                inserts = inserts,
                                                search_key = search_key,
                                                system_message = system_message,
                                                template = template)

                    # separate previously classified based on cache

                    new_messages = []
                    new_texts = []

                    for t_idx, text in enumerate(texts):

                        if (text in cats_cache.keys()) \
                            and (query in cats_cache[text][1] \
                                or query in cats_cache[text][0]):

                            if query in cats_cache[text][1]:

                                di_cats_update = {search_key : cats_cache[text][1]}
                                di_cats = inserts[t_idx].get("cats", {})
                                di_cats.update(di_cats_update)

                                previously_classified.update(
                                    {data_keys[t_idx] : {**inserts[t_idx] , "&cats" : di_cats}})
                            if query in cats_cache[text][0]:
                                previously_classified.update(
                                    {data_keys[t_idx] : inserts[t_idx]})
                        else:
                            new_messages.append(messages[t_idx])
                            new_texts.append(texts[t_idx])

                    if new_messages:

                        all_messages.append(new_messages)
                        all_cats_filtered.append({search_key : query})
                        all_texts.append({query : new_texts})


            all_cats_cache = {}
            all_filtered = {}

            if all_messages:

                # classify texts
                all_requests = [self._call_async_llm(messages = messages) \
                    for search_messages in all_messages for messages in search_messages]

                all_responses = await asyncio.gather(*all_requests)

                for m_id, cats in enumerate(all_cats_filtered):

                    responses = [all_responses[i] for i in range(m_id * len(data), (m_id + 1) * len(data))]

                    output_filter = self._extract_class_from_llm_output(responses=responses)
                    # filter data based on classification
                    filtered = self._filter_data(
                        data = data, 
                        output_filter = output_filter, 
                        cats = cats)
                    # prepare update for llm classification cache
                    all_cats_cache = self._update_all_cats_cache(
                        all_cats_cache = all_cats_cache,
                        output_filter = output_filter, 
                        texts = all_texts[m_id])

                    all_filtered.update(filtered)

            all_filtered.update(previously_classified)


        except Exception as e:
            self.logger.error(e)
            all_filtered = data
            all_cats_cache = {}

        return all_filtered, all_cats_cache
