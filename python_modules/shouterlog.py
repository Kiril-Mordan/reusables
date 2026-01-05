"""
This is an alternative logging module with extra capabilities.
It provides a method to output various types of lines and headers, with customizable message and line lengths, 
traces additional information and provides some debug capabilities based on that.
Its purpose is to be integrated into other classes that also use logger, primerally based on [`attrsx`](https://kiril-mordan.github.io/reusables/attrsx/).
"""

import logging
import inspect
from typing import List, Dict, Any
from datetime import datetime
import threading
import asyncio
import json
import os
import contextvars
import itertools
from functools import reduce
from operator import attrgetter
import dill #>=0.3.7
import attrs
import attrsx

from .components.shouterlog.asyncio_patch import patch_asyncio_proc_naming
from .components.shouterlog.log_plotter import LogPlotter

_MISSING = object()
_LOG_ID_COUNTER = itertools.count(1)
_TRACEBACK_CTX = contextvars.ContextVar("shouter_last_traceback", default=[])
_LAST_TASK_CTX = contextvars.ContextVar("shouter_last_task_name", default=None)


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
    'traceback_of_asyncio' : ['awaited functions would be different that processes spawned by asyncio and contain full traceback',
                    'to also have traceback for asyncio processes, some assumptions were made',
                    'each asyncio process is expected to be named and if spawned together should start with Proc-',
                    'last traceback would be used to augment traceback from asyncio which why it is important to log something before and after'],
    '_perform_action' : ['the method is currently does nothing but in the future could be used for user-defined actions']
}


# Metadata for package creation
__package_metadata__ = {
    "author": "Kyrylo Mordan",
    "author_email": "parachute.repo@gmail.com",
    "description": "A custom logging tool that expands normal logger with additional formatting and debug capabilities.",
    "keywords" : ['python', 'logging', 'debug tool']
}


patch_asyncio_proc_naming()

@attrsx.define(
    handler_specs = {"log_plotter" : LogPlotter},
    logger_chaining={
        'logger' : True
        }
)
class Shouter:

    """
    A class for managing and displaying formatted log messages.

    This class uses the logging module to create and manage a logger
    for displaying formatted messages. It provides a method to output
    various types of lines and headers, with customizable message and
    line lengths.
    """

    supported_classes = attrs.field(default=(), type = tuple)
    # Formatting settings
    dotline_length = attrs.field(default = 50, type = int)
    auto_output_type_selection = attrs.field(default = True, type = bool)
    show_function = attrs.field(default = True, type = bool)
    show_traceback = attrs.field(default = False, type = bool)
    show_idx = attrs.field(default = False, type = bool)
    # For saving records
    tears_persist_path = attrs.field(default='log_records.json')
    env_persist_path = attrs.field(default='environment.dill')
    datetime_format = attrs.field(default="%Y-%m-%d %H:%M:%S")
    log_records = attrs.field(factory=list, init=False)
    persist_env = attrs.field(default=False, type = bool)
    lock = attrs.field(default = None)
    last_traceback = attrs.field(factory=list)
   
    def __attrs_post_init__(self):
        self.lock = threading.Lock()
        self._reset_counter()

    __log_kwargs__ = {
        "output_type",
        "dotline_length",
        "auto_output_type_selection",
        "label",
        "save_vars"
    }

    def _reset_counter(self, start=1):
        global _LOG_ID_COUNTER
        _LOG_ID_COUNTER = itertools.count(start)

    def _format_mess(self,
                     mess : str,
                     label : str,
                     save_vars : list,
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

        tear = self._log_traceback(mess = mess,
                            label = label,
                            method = method,
                            save_vars = save_vars)

        output_type = self._select_output_type(mess = mess,
                                            output_type = output_type,
                                            auto_output_type_selection = auto_output_type_selection)


        out_mess = ""

        if self.show_function:
            out_mess += f"{tear['function']}:"

        if self.show_traceback:
            out_mess += f"{tear['traceback'][::-1]}:"

        out_mess += switch[output_type]()

        return out_mess


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


    def _log_traceback(self, mess: str, label : str, save_vars : list, method: str):
        """
        Active-stack semantics with explicit Proc handling.

        - Traceback order: LEAF -> ... -> ORIGIN
        - Non-proc logs define the true call chain.
        - Proc logs inherit parents because async stacks are incomplete.
        - Parents are NEVER resurrected after a non-proc step drops them.
        """

        functions = []
        lines = []

        supported_names = {
            (c if isinstance(c, type) else c.__class__).__name__
            for c in (self.supported_classes or ())
        }

        call_id = None

        # ---- collect current synchronous stack (leaf -> origin)
        for frame_info in inspect.stack():
            frame = frame_info.frame
            inst = frame.f_locals.get("self")
            if inst is None:
                continue

            cls_name = inst.__class__.__name__
            if cls_name not in supported_names:
                continue

            if call_id is None:
                call_id = id(frame)

            functions.append(f"{cls_name}.{frame.f_code.co_name}")
            lines.append(frame_info.lineno)

        # fallback if nothing matched
        if not functions:
            caller = inspect.currentframe().f_back
            call_id = id(caller)
            functions = [inspect.getframeinfo(caller).function]
            lines = [caller.f_lineno]

        # ---- asyncio / proc detection
        is_proc = False
        try:
            task = asyncio.current_task()
        except RuntimeError:
            task = None

        task_name = task.get_name() if task else None
        is_task = bool(task_name and task_name.startswith("Task-"))
        is_proc_task = bool(task_name and task_name.startswith("Proc-"))

        if is_proc_task:
            is_proc = True

        # include custom task name as pseudo-frame
        if task_name and not is_task and not is_proc_task:
            functions = functions + [task_name]

        # ---- context propagation (ContextVar-based)
        last_traceback = list(_TRACEBACK_CTX.get())

        if is_proc:
            # Proc: inherit parents (async stack is incomplete)
            if last_traceback:
                leaf = functions[0]
                parents = [f for f in last_traceback if f != leaf]
                functions = [leaf] + parents
        else:
            # Non-proc: authoritative stack, overwrite context
            pass

        # ---- dedupe, preserve order
        seen = set()
        out = []
        for f in functions:
            if f not in seen:
                out.append(f)
                seen.add(f)
        functions = out

        # update context ONLY with authoritative chain
        _TRACEBACK_CTX.set(list(functions))
        log_idx=next(_LOG_ID_COUNTER)

        env = {}
        if save_vars:
            env = self._get_local_vars(save_vars=save_vars, depth = 6)

        tear = {
            "idx" : log_idx,
            "call_id": call_id,
            "datetime": datetime.now().strftime(self.datetime_format),
            "level": method,
            "function": functions[0] if functions else [],
            "mess": mess,
            "line": lines[0] if lines else None,
            "lines": lines,
            "is_proc": is_proc,
            "proc_name" : task_name,
            "traceback": functions,
            "label" : label,
            "env" : env
        }

        self.log_records.append(tear)
        return tear

    def _persist_log_records(self):

        """
        Persists logs records into json file.
        """

        with self.lock:
            with open(self.tears_persist_path, 'a') as file:
                for tear in self.log_records:
                    tear_s = tear.copy()
                    if tear_s.get("env"):
                        tear_s["env"] = dict(self._filter_serializable(tear_s["env"], stype = "json"))
                    file.write(json.dumps(tear_s) + '\n')

    def _is_serializable(self,key,obj):

        """
        Check if object from env can be saved with dill, and if not, issue warning
        """

        try:
            dill.dumps(obj)
            return True
        except (TypeError, dill.PicklingError):
            return False

    def _is_json_serializable(self,key,obj):

        """
        Check if object from env can be saved with dill, and if not, issue warning
        """

        try:
            json.dumps({key : obj})
            return True
        except (TypeError, dill.PicklingError):
            return False


    def _filter_serializable(self,locals_dict, stype = "env"):
        """
        Filter the local variables dictionary, keeping only serializable objects.
        """
        if stype == "env":
            return {k: v for k, v in locals_dict.items() if self._is_serializable(k,v)}
        if stype == "json":
            return {k: v for k, v in locals_dict.items() if self._is_json_serializable(k,v)}


    def _get_local_vars(self, save_vars: list[str] = None, depth: int = 5):
        frame = inspect.currentframe()
        for _ in range(depth - 1):
            frame = frame.f_back

        locals_dict = frame.f_locals

        if not save_vars:
            return locals_dict

        def resolve(dotted: str):
            root, *parts = dotted.split(".")
            if root not in locals_dict:
                return _MISSING

            cur = locals_dict[root]
            for p in parts:
                try:
                    if isinstance(cur, dict):
                        cur = cur[p]
                    else:
                        cur = getattr(cur, p)
                except Exception:
                    return _MISSING
            return cur

        out = {}
        for name in save_vars:
            val = resolve(name)
            if val is not _MISSING:
                out[name] = val

        return out

    def _persist_environment(self):

        """
        Save the current environment variables using dill.
        """

        if self.persist_env:

            local_vars = self._get_local_vars()
            # filtering out local vars that cannot be saved with dill
            serializable_local_vars = dict(self._filter_serializable(local_vars))
            with self.lock:  # Ensure thread-safety if called from multiple threads
                with open(self.env_persist_path, 'wb') as file:
                    dill.dump(serializable_local_vars, file)


    def _perform_action(self,
                        method : str):

        return None

    def _log(self, 
             method, 
             mess : str = None,
             label : str = None,
             save_vars : list = None,
             dotline_length : int = None,
             output_type : str = None,
             auto_output_type_selection : bool = None,
             logger : logging.Logger = None,
             *args, **kwargs):

        if dotline_length is None:
            dotline_length = self.dotline_length

        if auto_output_type_selection is None:
            auto_output_type_selection = self.auto_output_type_selection

        if logger is None:
            logger = self.logger

        formated_mess = self._format_mess(mess = mess,
                                      label = label,
                                      dotline_length = dotline_length,
                                      output_type = output_type,
                                      method = method,
                                      save_vars = save_vars,
                                      auto_output_type_selection = auto_output_type_selection)

        if method == "info":
            logger.info(formated_mess,
                    *args, **kwargs)
        if method == "debug":
            logger.debug(formated_mess,
                    *args, **kwargs)
        if method == "warning":
            logger.warning(formated_mess,
                    *args, **kwargs)
        if method == "error":
            logger.error(formated_mess,
                    *args, **kwargs)
        if method == "fatal":
            logger.fatal(formated_mess,
                    *args, **kwargs)
        if method == "critical":
            logger.critical(formated_mess,
                    *args, **kwargs)

        if method in ["error", "fatal", "critical"]:

            self._persist_log_records()
            self._persist_environment()


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

    def show_sequence_diagram(self, 
                              log_records : List[Dict[str, Any]] = None, 
                              *args, **kwargs):

        if log_records is None:
            log_records = self.log_records

        if log_records:

            self._initialize_log_plotter_h()

            self.log_plotter_h.plot_sequence_diagram_from_tracebacks(
                log_records = log_records,
                *args, **kwargs
            )
        else:
            self.warning("No log records were provided!")

    def show_logs_by_id(self, ids : List[int]):

        return [i for i in self.log_records if i.get("idx", 0) in ids ]


    def info(self,
             mess : str = None,
             dotline_length : int = None,
             output_type : str = None,
             auto_output_type_selection : bool = None,
             label : str = None,
             save_vars : list = None,
             logger : logging.Logger = None,
             *args, **kwargs) -> None:

        """
        Prints info message similar to standard logger but with types of output and some additional actions.
        """

        self._log(
            method = "info",
            mess = mess,
            dotline_length = dotline_length,
            output_type = output_type,
            auto_output_type_selection = auto_output_type_selection,
            label = label,
            save_vars = save_vars,
            logger = logger,
            *args, **kwargs
        )

    def debug(self,
             mess : str = None,
             dotline_length : int = None,
             output_type : str = None,
             auto_output_type_selection : bool = None,
             label : str = None,
             save_vars : list = None,
             logger : logging.Logger = None,
             *args, **kwargs) -> None:

        """
        Prints debug message similar to standard logger but with types of output and some additional actions.
        """


        self._log(
            method = "debug",
            mess = mess,
            dotline_length = dotline_length,
            output_type = output_type,
            auto_output_type_selection = auto_output_type_selection,
            label = label,
            save_vars = save_vars,
            logger = logger,
            *args, **kwargs
        )

    def warning(self,
             mess : str = None,
             dotline_length : int = None,
             output_type : str = None,
             auto_output_type_selection : bool = None,
             label : str = None,
             save_vars : list = None,
             logger : logging.Logger = None,
             *args, **kwargs) -> None:

        """
        Prints warning message similar to standard logger but with types of output and some additional actions.
        """


        self._log(
            method = "warning",
            mess = mess,
            dotline_length = dotline_length,
            output_type = output_type,
            auto_output_type_selection = auto_output_type_selection,
            label = label,
            save_vars = save_vars,
            logger = logger,
            *args, **kwargs
        )

    def error(self,
             mess : str = None,
             dotline_length : int = None,
             output_type : str = None,
             auto_output_type_selection : bool = None,
             label : str = None,
             save_vars : list = None,
             logger : logging.Logger = None,
             *args, **kwargs) -> None:

        """
        Prints error message similar to standard logger but with types of output and some additional actions.
        """

        self._log(
            method = "error",
            mess = mess,
            dotline_length = dotline_length,
            output_type = output_type,
            auto_output_type_selection = auto_output_type_selection,
            label = label,
            save_vars = save_vars,
            logger = logger,
            *args, **kwargs
        )

    def fatal(self,
             mess : str = None,
             dotline_length : int = None,
             output_type : str = None,
             auto_output_type_selection : bool = None,
             label : str = None,
             save_vars : list = None,
             logger : logging.Logger = None,
             *args, **kwargs) -> None:

        """
        Prints fatal message similar to standard logger but with types of output and some additional actions.
        """


        self._log(
            method = "fatal",
            mess = mess,
            dotline_length = dotline_length,
            output_type = output_type,
            auto_output_type_selection = auto_output_type_selection,
            label = label,
            save_vars = save_vars,
            logger = logger,
            *args, **kwargs
        )

    def critical(self,
             mess : str = None,
             dotline_length : int = None,
             output_type : str = None,
             auto_output_type_selection : bool = None,
             label : str = None,
             save_vars : list = None,
             logger : logging.Logger = None,
             *args, **kwargs) -> None:

        """
        Prints critical message similar to standard logger but with types of output and some additional actions.
        """

        self._log(
            method = "critical",
            mess = mess,
            dotline_length = dotline_length,
            output_type = output_type,
            auto_output_type_selection = auto_output_type_selection,
            label = label,
            save_vars = save_vars,
            logger = logger,
            *args, **kwargs
        )
