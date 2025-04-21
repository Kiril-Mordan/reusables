import logging
import asyncio
import os
from abc import ABC, abstractmethod
from typing import Optional, List, Dict
import attrs #>=23.1.0
import attrsx

#! import openai
#! import ollama


@attrsx.define(kw_only=True)
class BaseLlmHandler(ABC):

    """
    Base class should be used to extend LLM handler with new connection clients.
    """

    registry = {}

    def __init_subclass__(cls, **kwargs):

        """
        Registers subclasses that inherit from BaseLlmHandler
        """

        super().__init_subclass__(**kwargs)
        BaseLlmHandler.registry[cls.__name__] = cls


    @abstractmethod
    async def chat_async(self, 
        messages: List[Dict[str, str]], 
        model_name: Optional[str] = None) -> dict:

        """
        Every llm connection class that inherits from BaseLlmHandler is expected to have async method 
        to push a list of messages and model name, returing a dictionary with responses.
        """


@attrsx.define(kw_only=True)
class OllamaConn(BaseLlmHandler):

    # pylint: disable=import-outside-toplevel

    """
    Extended OllamaHandlerAsync supporting chat with optional function calling.
    """

    connection_string: Optional[str] = attrs.field(default=None)
    model_name: Optional[str] = attrs.field(default="llama3.1:latest")

    model = attrs.field(default=None)

    kwargs: dict = attrs.field(factory=dict)

    def __attrs_post_init__(self):
        self._initialize_ollama()

    def _initialize_ollama(self):

        try:
            from ollama import AsyncClient
        except ImportError as e:
            self.logger.error("Failed to import ollama!")
            raise e

        if self.model is None:
            self.model = AsyncClient(
                host = self.connection_string, 
                **self.kwargs)


    async def chat_async(self, 
                   messages: List[Dict[str, str]], 
                   model_name: Optional[str] = None) -> Dict:
        """
        Core chat method for interacting with Ollama api.
        """

        params = {
            "model": model_name or self.model_name,
            "messages": messages,
            **self.kwargs
        }

        response = await self.model.chat(**params)
        self.logger.debug(f"Tokens used: {response.get('usage', {}).get('total_tokens', 0)}")
        
        # Convert response to dict
        response_dict = {
            "model": response.model,
            "created_at": response.created_at,
            "done": response.done,
            "done_reason": response.done_reason,
            "total_duration": response.total_duration,
            "load_duration": response.load_duration,
            "prompt_eval_count": response.prompt_eval_count,
            "prompt_eval_duration": response.prompt_eval_duration,
            "eval_count": response.eval_count,
            "eval_duration": response.eval_duration,
            "choices" : [{"message": {
                "role": response.message.role,
                "content": response.message.content,
            }}
            ]
        }

        return response_dict
            

@attrsx.define(kw_only=True)
class OpenAIConn(BaseLlmHandler):

    # pylint: disable=import-outside-toplevel

    """
    OpenAIHandlerAsync - Async client for OpenAI models with native function calling (tools).
    """

    connection_string: Optional[str] = attrs.field(default=None)  # Optional for Azure OpenAI
    model_name: Optional[str] = attrs.field(default="gpt-4o-mini")  # Default OpenAI model
    api_key: Optional[str] = attrs.field(default=None)  # OpenAI API Key

    model = attrs.field(default=None)
    
    kwargs: dict = attrs.field(factory=dict)  # Additional passthrough options

    def __attrs_post_init__(self):
        self._initialize_openai()

    def _initialize_openai(self):

        try:
            from openai import AsyncOpenAI
        except ImportError as e:
            self.logger.error("Failed to import openai!")

            raise e

        if self.model is None:

            params = {}

            if self.api_key:
                params['api_key'] = self.api_key
            if self.connection_string:
                params['api_base'] = self.connection_string  # Support for Azure endpoint

            self.model = AsyncOpenAI(
                **params
            )

    async def chat_async(self, 
                   messages: List[Dict[str, str]], 
                   model_name: Optional[str] = None) -> Dict:
        """
        Core chat method for interacting with OpenAI api.
        """

        params = {
            "model": model_name or self.model_name,
            "messages": messages,
            **self.kwargs
        }
        
        response = await self.model.chat.completions.create(**params)
        response = response.model_dump()
        self.logger.debug(f"Tokens used: {response['usage']['total_tokens']}")
        
        # Convert response to dict
        response_dict = {
            "model": response["model"],
            "created_at": response["created"],
            "choices": response["choices"],
            "usage": response["usage"]
        }
        
        return response_dict


@attrsx.define
class LlmHandler:

    # pylint: disable=unsubscriptable-object
    # pylint: disable=unsupported-assignment-operation
    # pylint: disable=unsupported-delete-operation

    """
    General llm handler, connects to different llm apis.
    """

    llm_h_type : str = attrs.field(default='OllamaConn')
    llm_h_params : dict = attrs.field(default={})
    
    llm_h_class = attrs.field(default = None)
    llm_h = attrs.field(default = None)

    instance : "BaseLlmHandler" = attrs.field(init=False)

    def __attrs_post_init__(self):

        self._initialize_llm_h()

    def _initialize_llm_h(self):

        if self.llm_h is None:

            if "env_mapping" in self.llm_h_params.keys():

                for key, value in self.llm_h_params["env_mapping"].items():
                    self.llm_h_params[key] = os.getenv(value)

                del self.llm_h_params["env_mapping"]

            self.llm_h = BaseLlmHandler.registry[self.llm_h_type](**self.llm_h_params)

    async def chat(self, 
                   messages: List[Dict[str, str]], 
                   model_name: Optional[str] = None) -> Dict:
        """
        Core chat method to interact with selected client.
        """
        
        try:

            response = await self.llm_h.chat_async(
                messages = messages,
                model_name = model_name)

        except Exception as e:
            response = None
            self.logger.error(f"LLM Handler Error: {e}")

        return response
