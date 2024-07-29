import logging
import attrs #==23.2.0
from ollama import AsyncClient, Client #==0.2.1
from typing import Any, AnyStr, Union, Optional, Sequence, Mapping, Literal, overload, Callable, Dict


@attrs.define
class OllamaHandlerAsync(AsyncClient):

    """
    OllamaHandlerAsync is a simple connector to ollama.AsyncClient
    meant to with LlmHandlerAsync in the role of llm_handler.
    """

    connection_string: Optional[str] = attrs.field(default=None)

    model_name : Optional[str] = attrs.field(default=None)

    # Logger settings
    logger = attrs.field(default=None)
    logger_name = attrs.field(default="Ollama Handler Async")
    loggerLvl = attrs.field(default=logging.INFO)
    logger_format = attrs.field(default=None)

    # Passthrough options
    kwargs: dict = attrs.field(factory=dict)
    
    def __attrs_post_init__(self):
        super().__init__(host=self.connection_string, **self.kwargs)
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


    async def chat(self,
                    messages : list, 
                model_name : str = None):

        """
        Async chat method from ollama.AsyncClient extended with message history and optional token usage counter.
        """
        
        # request chat
        response = await super().chat(
            model=model_name or self.model_name, 
            messages=messages)


        return response

    async def generate(self,
                    prompt : str, 
                model_name : str = None):

        """
        Async chat method from ollama.AsyncClient extended with message history and optional token usage counter.
        """
        
        # request chat
        response = await super().generate(
            model=model_name or self.model_name, 
            prompt=prompt)


        return response