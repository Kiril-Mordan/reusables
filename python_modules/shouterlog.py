"""
Shouter Log

This class uses the logging module to create and manage a logger for displaying formatted messages.
It provides a method to output various types of lines and headers, with customizable message and line lengths.
The purpose is to be integrated into other classes that also use logger.
"""


import logging
import inspect
from datetime import datetime
import attr #>=22.2.0
import threading
import dill #==0.3.7
import json
import os

__design_choices__ = {
    'logger' : ['underneath shouter is a standard logging so a lot of its capabilities were preserved',
                'custom loggers can be used within shouter, if not it will define one on its own',
                'from normal logging only the commands to log are available'],
    '_format_mess' : ['_format_mess is method where all the predefined custom formats are curretly implemented',
                      '_format_mess method triggeres _select_output_type',
                      'any parameters _select_output_type needs should be passed through class def or the method'],
    '_select_output_type' : ['the type should be selecting automatically in the future based on tracebacks'],
    'supported_classes' : ['supported classes is a required parameter if shouter is to be used within a class',
                           'supported classes is a parameter where all the classes that it visits should be listed',
                           'not listing classes would limit ability of shouter to create readable tracebacks'],
    'debbuging_capabilities' : ['issuing error, critical or fatal will optionally allow to save local variables',
                                'local variables will saved on the level of shouter statement',
                                'object that would be persisted are the ones that could be serialized',
                                'waring statement will apear for the ones that could not be save will dill'],
    'persist_state' : ['persist state happends automatically for logger lvls: error, critical/fatal',
                       'persist state can triggered manually with persist_state funtion',
                       'persist state can potentially perform two things: save tears (logs) and save os.environ',
                       'persisting tears happends in a form of json file',
                       'persisting os.environ happends in a form of dill file',
                       'persisting os.environ is optional and by defaul set to False'],
    '_perform_action' : ['the method is currently does nothing but in the future could be used for user-defined actions']
}


# Metadata for package creation
__package_metadata__ = {
    "author": "Kyrylo Mordan",
    "author_email": "parachute.repo@gmail.com",
    "description": "A custom logging tool that expands normal logger with additional formatting and debug capabilities.",
    "keywords" : ['python', 'logging', 'debug tool']
}



@attr.s
class Shouter:

    """
    A class for managing and displaying formatted log messages.

    This class uses the logging module to create and manage a logger
    for displaying formatted messages. It provides a method to output
    various types of lines and headers, with customizable message and
    line lengths.
    """

    supported_classes = attr.ib(default=(), type = tuple)
    # Formatting settings
    dotline_length = attr.ib(default = 50, type = int)
    auto_output_type_selection = attr.ib(default = True, type = bool)
    # For saving records
    tears_persist_path = attr.ib(default='log_records.json')
    env_persist_path = attr.ib(default='environment.dill')
    datetime_format = attr.ib(default="%Y-%m-%d %H:%M:%S")
    log_records = attr.ib(factory=list, init=False)
    persist_env = attr.ib(default=False, type = bool)

    # Logger settings
    logger = attr.ib(default=None)
    logger_name = attr.ib(default='Shouter')
    loggerLvl = attr.ib(default=logging.DEBUG)
    logger_format = attr.ib(default='(%(asctime)s) : %(name)s : [%(levelname)s] : %(message)s')

    def __attrs_post_init__(self):
        self.initialize_logger()
        self.lock = threading.Lock()

    def initialize_logger(self):

        """
        Initialize a logger for the class instance based on
        the specified logging level and logger name.
        """

        if self.logger is None:
            logging.basicConfig(level=self.loggerLvl,format=self.logger_format)
            logger = logging.getLogger(self.logger_name)
            logger.setLevel(self.loggerLvl)

            self.logger = logger

    def _format_mess(self,
                     mess : str,
                     dotline_length : int,
                     output_type : str,
                     method : str,
                     auto_output_type_selection : bool):

        """
        Format message before it is passed to be displayed.
        """

        switch = {
            "default" : lambda : mess,
            "dline": lambda: "=" * dotline_length,
            "line": lambda: "-" * dotline_length,
            "pline": lambda: "." * dotline_length,
            "HEAD1": lambda: "".join(["\n",
                                        "=" * dotline_length,
                                        "\n",
                                        "-" * ((dotline_length - len(mess)) // 2 - 1),
                                        mess,
                                        "-" * ((dotline_length - len(mess)) // 2 - 1),
                                        " \n",
                                        "=" * dotline_length]),
            "HEAD2": lambda: "".join(["\n",
                                        "*" * ((dotline_length - len(mess)) // 2 - 1),
                                        mess,
                                        "*" * ((dotline_length - len(mess)) // 2 - 1)]),
            "HEAD3": lambda: "".join(["\n",
                                        "/" * ((dotline_length - 10 - len(mess)) // 2 - 1),
                                        mess,
                                        "\\" * ((dotline_length - 10 - len(mess)) // 2 - 1)]),
            "title": lambda: f"** {mess}",
            "subtitle": lambda: f"*** {mess}",
            "subtitle0": lambda: f"+ {mess}",
            "subtitle1": lambda: f"++ {mess}",
            "subtitle2": lambda: f"+++ {mess}",
            "subtitle3": lambda: f"++++ {mess}",
            "warning": lambda: f"!!! {mess}",
        }

        self._log_traceback(mess = mess,
                            method = method)

        output_type = self._select_output_type(mess = mess,
                                            output_type = output_type,
                                            auto_output_type_selection = auto_output_type_selection)

        return switch[output_type]()


    def _select_output_type(self,
                              mess : str,
                              output_type : str,
                              auto_output_type_selection : bool):

        """
        Based on message and some other information, select output_type.
        """

        # select output type automatically if condition is triggered
        if auto_output_type_selection:

            # determining traceback size of last tear
            traceback_size = len(self.log_records[-1]['traceback'])
        else:
            # otherwise set traceback_size to one
            traceback_size = 1

        if output_type is None:

            if mess is not None:

                # use traceback size to select output_type is message is available

                if traceback_size > 4:
                    return 'subtitle3'

                if traceback_size > 3:
                    return 'subtitle2'

                if traceback_size > 2:
                    return 'subtitle1'

                if traceback_size > 1:
                    return 'subtitle0'

                return 'default'

            else:

                # use traceback size to select output_type is message is not available

                if traceback_size > 2:
                    return "pline"

                if traceback_size > 1:
                    return "line"

                return "dline"

        return output_type


    def _log_traceback(self,
                       mess : str,
                       method : str):

        """
        Keeps records of every use of log statement.
        """

        current_frame = inspect.currentframe().f_back
        functions = []
        lines = []

        # Iterate through frames and capture relevant ones
        while current_frame:
            if 'self' in current_frame.f_locals:
                # Instance method
                instance = current_frame.f_locals['self']
                class_name = instance.__class__.__name__
                method_name = current_frame.f_code.co_name
                full_function_name = f"{class_name}.{method_name}"

                # Append only if it belongs to your application's classes
                if isinstance(instance, self.supported_classes):  # Replace with your actual class names
                    functions.append(full_function_name)
                    lines.append(current_frame.f_lineno)

            current_frame = current_frame.f_back

        # If no relevant traceback is found, use the immediate caller
        if not functions:
            caller_frame = inspect.currentframe().f_back
            functions.append(inspect.getframeinfo(caller_frame).function)
            lines.append(caller_frame.f_lineno)

        tear = {
            'datetime' : datetime.now().strftime(self.datetime_format),
            'level': method,
            'function' : functions[-1],
            'mess': mess,
            'line' : lines[-1],
            'lines' : lines,
            'traceback': functions
        }

        self.log_records.append(tear)

    def _persist_log_records(self):

        """
        Persists logs records into json file.
        """

        with self.lock:
            with open(self.tears_persist_path, 'a') as file:
                for tear in self.log_records:
                    file.write(json.dumps(tear) + '\n')

    def _is_serializable(self,key,obj):

        """
        Check if object from env can be saved with dill, and if not, issue warning
        """

        try:
            dill.dumps(obj)
            return True
        except (TypeError, dill.PicklingError):
            self.logger.warning(f"Object '{key}' could not have been serialized, when saving last words!")
            return False


    def _filter_serializable(self,locals_dict):
        """
        Filter the local variables dictionary, keeping only serializable objects.
        """
        return {k: v for k, v in locals_dict.items() if self._is_serializable(k,v)}


    def _persist_environment(self):

        """
        Save the current environment variables using dill.
        """

        if self.persist_env:

            # using double f_back to get to the level where shouter is called
            caller_frame = inspect.currentframe().f_back.f_back
            # extracting local vars
            local_vars = caller_frame.f_locals
            # filtering out local vars that cannot be saved with dill
            serializable_local_vars = dict(self._filter_serializable(local_vars))

            with self.lock:  # Ensure thread-safety if called from multiple threads
                with open(self.env_persist_path, 'wb') as file:
                    dill.dump(serializable_local_vars, file)

    def persist_state(self,
                      tears_persist_path : str = None,
                      env_persist_path : str = None):

        """
        Function for persisting state inteded to be used to extract logs and manually save env.
        """

        # temporarily overwriting class persist paths
        if tears_persist_path is not None:
            prev_tears_persist_path = self.tears_persist_path
            self.tears_persist_path = tears_persist_path
        else:
            prev_tears_persist_path = None

        if env_persist_path is not None:
            prev_env_persist_path = self.env_persist_path
            self.env_persist_path = env_persist_path
        else:
            prev_env_persist_path = None

        # persisting state
        self._persist_log_records()
        self._persist_environment()

        # revert to predefined path for persisting after persist was complete
        if prev_tears_persist_path:
            self.tears_persist_path = prev_tears_persist_path
        if prev_env_persist_path:
            self.env_persist_path = prev_env_persist_path



    def return_logged_tears(self):

        """
        Return list of dictionaries of log records.
        """

        return self.log_records

    def return_last_words(self,
                          env_persist_path : str = None):

        """
        Return debug environment.
        """

        if env_persist_path is None:
            env_persist_path = self.env_persist_path

        with open(env_persist_path, 'rb') as file:
            debug_env = dill.load(file)

        return debug_env


    def _perform_action(self,
                        method : str):

        return None


    def info(self,
             mess : str = None,
             dotline_length : int = None,
             output_type : str = None,
             auto_output_type_selection : bool = None,
             logger : logging.Logger = None,
             *args, **kwargs) -> None:

        """
        Prints info message similar to standard logger but with types of output and some additional actions.
        """


        if dotline_length is None:
            dotline_length = self.dotline_length

        if auto_output_type_selection is None:
            auto_output_type_selection = self.auto_output_type_selection

        if logger is None:
            logger = self.logger

        formated_mess = self._format_mess(mess = mess,
                                      dotline_length = dotline_length,
                                      output_type = output_type,
                                      method = 'info',
                                      auto_output_type_selection = auto_output_type_selection)

        logger.info(formated_mess,
                    *args, **kwargs)

    def debug(self,
             mess : str = None,
             dotline_length : int = None,
             output_type : str = None,
             auto_output_type_selection : bool = None,
             logger : logging.Logger = None,
             *args, **kwargs) -> None:

        """
        Prints debug message similar to standard logger but with types of output and some additional actions.
        """


        if dotline_length is None:
            dotline_length = self.dotline_length

        if auto_output_type_selection is None:
            auto_output_type_selection = self.auto_output_type_selection

        if logger is None:
            logger = self.logger

        formated_mess = self._format_mess(mess = mess,
                                      dotline_length = dotline_length,
                                      output_type = output_type,
                                      method = 'debug',
                                      auto_output_type_selection = auto_output_type_selection)

        logger.debug(formated_mess,
                     *args, **kwargs)

    def warning(self,
             mess : str = None,
             dotline_length : int = None,
             output_type : str = None,
             auto_output_type_selection : bool = None,
             logger : logging.Logger = None,
             *args, **kwargs) -> None:

        """
        Prints warning message similar to standard logger but with types of output and some additional actions.
        """


        if dotline_length is None:
            dotline_length = self.dotline_length

        if auto_output_type_selection is None:
            auto_output_type_selection = self.auto_output_type_selection

        if logger is None:
            logger = self.logger

        formated_mess = self._format_mess(mess = mess,
                                      dotline_length = dotline_length,
                                      output_type = output_type,
                                      method = 'warning',
                                      auto_output_type_selection = auto_output_type_selection)

        logger.warning(formated_mess,
                       *args, **kwargs)

    def error(self,
             mess : str = None,
             dotline_length : int = None,
             output_type : str = None,
             auto_output_type_selection : bool = None,
             logger : logging.Logger = None,
             *args, **kwargs) -> None:

        """
        Prints error message similar to standard logger but with types of output and some additional actions.
        """


        if dotline_length is None:
            dotline_length = self.dotline_length

        if auto_output_type_selection is None:
            auto_output_type_selection = self.auto_output_type_selection

        if logger is None:
            logger = self.logger

        formated_mess = self._format_mess(mess = mess,
                                      dotline_length = dotline_length,
                                      output_type = output_type,
                                      method = 'error',
                                      auto_output_type_selection = auto_output_type_selection)

        logger.error(formated_mess,
                     *args, **kwargs)

        self._persist_log_records()
        self._persist_environment()

    def fatal(self,
             mess : str = None,
             dotline_length : int = None,
             output_type : str = None,
             auto_output_type_selection : bool = None,
             logger : logging.Logger = None,
             *args, **kwargs) -> None:

        """
        Prints fatal message similar to standard logger but with types of output and some additional actions.
        """


        if dotline_length is None:
            dotline_length = self.dotline_length

        if auto_output_type_selection is None:
            auto_output_type_selection = self.auto_output_type_selection

        if logger is None:
            logger = self.logger

        formated_mess = self._format_mess(mess = mess,
                                      dotline_length = dotline_length,
                                      output_type = output_type,
                                      method = 'fatal',
                                      auto_output_type_selection = auto_output_type_selection)

        logger.fatal(formated_mess,
                     *args, **kwargs)

        self._persist_log_records()
        self._persist_environment()

    def critical(self,
             mess : str = None,
             dotline_length : int = None,
             output_type : str = None,
             auto_output_type_selection : bool = None,
             logger : logging.Logger = None,
             *args, **kwargs) -> None:

        """
        Prints critical message similar to standard logger but with types of output and some additional actions.
        """


        if dotline_length is None:
            dotline_length = self.dotline_length

        if auto_output_type_selection is None:
            auto_output_type_selection = self.auto_output_type_selection

        if logger is None:
            logger = self.logger

        formated_mess = self._format_mess(mess = mess,
                                      dotline_length = dotline_length,
                                      output_type = output_type,
                                      method = 'critical',
                                      auto_output_type_selection = auto_output_type_selection)

        logger.critical(formated_mess,
                        *args, **kwargs)

        self._persist_log_records()
        self._persist_environment()

