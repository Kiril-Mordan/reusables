"""
Proompter

Wrapper for llm calls, meant for experimentation with different prompt and history 
handling strategies.
"""

import logging
import asyncio 
import time
from transformers import AutoTokenizer #==4.43.2
from huggingface_hub import login #==0.24.2
from typing import Any, AnyStr, Union, Optional, Sequence, Mapping, Literal, overload, Callable, Dict
import attrs #==23.2.0

from .components.proompter.ollama import OllamaHandlerAsync
from .components.proompter.prompt_strategies import PromptStrategyHandler, PromptHandler

# Metadata for package creation
__package_metadata__ = {
    "author": "Kyrylo Mordan",
    "author_email": "parachute.repo@gmail.com",
    "description": "Simple wrapper around some Llm handlers.",
}



@attrs.define
class HfTokenizerHandler():

    """
    HfTokenizerHandler is a wrapper to use Tokenizers from Huggingface.
    """

    access_token : Optional[str] = attrs.field(default=None)
    use_auth_token : Optional[bool] = attrs.field(default=None)
    tokenizer_name : Optional[str] = attrs.field(default=None)

    tokenizer = attrs.field(default=None)

    # Logger settings
    logger = attrs.field(default=None)
    logger_name = attrs.field(default='HF Tokenizer')
    loggerLvl = attrs.field(default=logging.INFO)
    logger_format = attrs.field(default=None)

    def __attrs_post_init__(self):
        self._initialize_logger()

        # authenticate to access hugginface
        if self.access_token:
            login(self.access_token)
            self.use_auth_token = True
        else:
            self.use_auth_token = False

    def _initialize_logger(self):

        """
        Initialize a logger for the class instance based on the specified logging level and logger name.
        """

        if self.logger is None:
            logging.basicConfig(level=self.loggerLvl, format=self.logger_format)
            logger = logging.getLogger(self.logger_name)
            logger.setLevel(self.loggerLvl)

            self.logger = logger

    def tokenize(self, text : str):

        """
        Tokenize text.
        """

        if self.tokenizer is None:
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.tokenizer_name, 
                use_auth_token = self.use_auth_token)
        

        return self.tokenizer.tokenize(str(text))


@attrs.define
class Proompter():

    """
    Proompter is meant as a wrapper around some Llm handlers.
    Its purpose is to serve as extension component that abstract their usage.

    Proompter consists of multiple dependecies, which could be initialized and passed to the class externally or parameters could be passed for class to initialize them.

    These include:

        - LLM handler: makes calls to llm
        - Prompt handler: prepares input based on templates
        - Prompt strategy handler: contains ways to call llm handler with selected strategy
        - Tokenizer handler: tokenizes text
    """

    # Dependencies
    llm_handler_class = attrs.field(default=OllamaHandlerAsync)
    prompt_handler_class = attrs.field(default=PromptHandler)
    tokenizer_handler_class = attrs.field(default=HfTokenizerHandler)
    call_strategy_handler_class = attrs.field(default=PromptStrategyHandler)

    # Instances
    llm_handler_h = attrs.field(default=None)
    tokenizer_h = attrs.field(default=None)
    prompt_h = attrs.field(default=None)
    call_strategy_h = attrs.field(default=None)

    # Dependecies params
    llm_h_params = attrs.field(default={})
    prompt_h_params = attrs.field(default={})
    call_strategy_h_params = attrs.field(default={})
    tokenizer_h_params = attrs.field(default={})

    # Chat history
    messages : Optional[list] = attrs.field(default=None)
    responses : Optional[list] = attrs.field(default=[])

    # Logger settings
    logger = attrs.field(default=None)
    logger_name = attrs.field(default='Llm Handler Async')
    loggerLvl = attrs.field(default=logging.INFO)
    logger_format = attrs.field(default=None)
    
    def __attrs_post_init__(self):

        self._initialize_logger()
        self._initialize_llm_handler()
        self._initialize_prompt_handler()
        self._initialize_call_strategy_handler()
        self._initialize_tokenizer_handler()


    def _initialize_logger(self):

        """
        Initialize a logger for the class instance based on the specified logging level and logger name.
        """

        if self.logger is None:
            logging.basicConfig(level=self.loggerLvl, format=self.logger_format)
            logger = logging.getLogger(self.logger_name)
            logger.setLevel(self.loggerLvl)

            self.logger = logger

    def _initialize_llm_handler(self):

        """
        Initialize llm handler instance with provided parameters
        """

        if self.llm_handler_h is None:

            self.llm_handler_h = self.llm_handler_class(
                **self.llm_h_params,
                logger = self.logger
            )

    def _initialize_prompt_handler(self):

        """
        Initialize prompt handler instance with provided parameters
        """

        if self.prompt_h is None:
            self.prompt_h = self.prompt_handler_class(
                **self.prompt_h_params,
                logger = self.logger
            )

    def _initialize_call_strategy_handler(self):

        """
        Initialize call stetegy handler instance with provided parameters
        """

        self.call_strategy_h = self.call_strategy_handler_class(
            **self.call_strategy_h_params,
            logger = self.logger
        )

    def _initialize_tokenizer_handler(self):

        """
        Initialize llm handler instance with provided parameters
        """

        if self.tokenizer_h_params != {}:

            self.tokenizer_h = self.tokenizer_handler_class(
                **self.tokenizer_h_params,
                logger = self.logger)
        
    def estimate_tokens(self, text : str):

        """
        Estimate number of tokens for provided text with defined tokenizer
        """

        if self.tokenizer_h:
            return len(self.tokenizer_h.tokenize(text = text))
        else:
            self.logger.warning("Tokenizer was not defined, estimation will be skipped!")
            return None

    async def prompt_chat(self,
                    messages : list, 
                    model_name : str = None,
                    prompt_templates : dict = None,
                    call_strategy_name : str = None,
                    call_strategy_params : dict = None):

        """
        Async prompt method extended with message history and optional token usage counter.
        """

        if prompt_templates is None:
            prompt_templates = self.prompt_h_params.get(
                'template', None)

        if model_name is None: 
            model_name = self.llm_h_params.get(
                'model_name', None) 

        if call_strategy_name is None:
            call_strategy_name = self.call_strategy_h_params.get(
                'strategy_name', None)

        if call_strategy_params is None:
            call_strategy_params = self.call_strategy_h_params.get(
                'strategy_params', None)

        messages = messages.copy()

        # apply prompt template
        processed_messages = self.prompt_h.apply_template(
            messages=messages,
            template=prompt_templates)


        # prompting chat
        start_time = time.time()
        response = await self.call_strategy_h.call_async(
            function = self.llm_handler_h.chat,
            strategy_name = call_strategy_name,
            strategy_params = call_strategy_params,
            messages = processed_messages, 
            model_name = model_name
        ) 
        end_time = time.time()

        # save response time
        response['response_time'] = end_time - start_time

        # save message history
        messages.append(response['message'])
        response['messages'] = self.prompt_h.apply_template(
            messages=messages,
            template=prompt_templates)


        # calculating token usage
        input_tokens = self.estimate_tokens(text=messages)
        output_tokens = self.estimate_tokens(text=response['message']['content'])
        
        if input_tokens and output_tokens:
            total_tokens = input_tokens + output_tokens
        else:
            total_tokens = None

        response['input_tokens'] = input_tokens
        response['output_tokens'] = output_tokens
        response['total_tokens'] = total_tokens

        # saving responses
        self.messages = messages
        self.responses.append(response)

        return response

    async def prompt_instruct(self,
                    prompt : list, 
                    model_name : str = None,
                    call_strategy_name : str = None,
                    call_strategy_params : dict = None):

        """
        Async prompt method to run instruct models.
        """

        if model_name is None: 
            model_name = self.llm_h_params.get(
                'model_name', None) 

        if call_strategy_name is None:
            call_strategy_name = self.call_strategy_h_params.get(
                'strategy_name', None)

        if call_strategy_params is None:
            call_strategy_params = self.call_strategy_h_params.get(
                'strategy_params', None)

        # prompting chat
        start_time = time.time()
        response = await self.call_strategy_h.call_async(
            function = self.llm_handler_h.generate,
            strategy_name = call_strategy_name,
            strategy_params = call_strategy_params,
            prompt = prompt, 
            model_name = model_name
        ) 
        end_time = time.time()

        # save response time
        response['response_time'] = end_time - start_time

        # calculating token usage
        input_tokens = self.estimate_tokens(text=prompt)
        output_tokens = self.estimate_tokens(text=response['response'])
        
        if input_tokens and output_tokens:
            total_tokens = input_tokens + output_tokens
        else:
            total_tokens = None

        response['input_tokens'] = input_tokens
        response['output_tokens'] = output_tokens
        response['total_tokens'] = total_tokens

        # saving responses
        self.responses.append(response)

        return response

    async def prompt_chat_parallel(self,
                                    messages : list, 
                                    model_name : str = None,
                                    prompt_templates : dict = None,
                                    call_strategy_name : str = None,
                                    call_strategy_params : dict = None):

        """
        Async prompt method that processes each message independently in parallel
        """

        messages = messages.copy()
        
        response_calls = [self.prompt_chat(messages = messages_list, 
                                    model_name = model_name,
                                    prompt_templates = prompt_templates,
                                    call_strategy_name = call_strategy_name,
                                    call_strategy_params = call_strategy_params) \
                                        for messages_list in messages]

        responses = await asyncio.gather(*response_calls)                            

        return responses

    async def prompt_instruct_parallel(self,
                                    prompts : list, 
                                    model_name : str = None,
                                    call_strategy_name : str = None,
                                    call_strategy_params : dict = None):

        """
        Async prompt method that processes each prompt independently in parallel
        """
        
        response_calls = [self.prompt_instruct(prompt = prompt, 
                                    model_name = model_name,
                                    call_strategy_name = call_strategy_name,
                                    call_strategy_params = call_strategy_params) \
                                        for prompt in prompts]

        responses = await asyncio.gather(*response_calls)                            

        return responses

    async def chat(self, 
                   prompt : str, 
                   new_dialog : bool = False):

        """
        Async chat method to pass new prompts and manage history.
        """


        if self.messages is None:
            messages = []
        else:
            messages = self.messages.copy()

        if new_dialog:
            messages = []

        messages.append({'role': 'user', 'content': prompt})

        response = await self.prompt_chat(
            messages = messages)

        return response['message']['content']

