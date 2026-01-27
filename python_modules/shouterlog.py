"""
This is an alternative logging module with extra capabilities.
It provides a method to output various types of lines and headers, with customizable message and line
lengths, 
traces additional information and provides debug capabilities and optional persistence based on that.
Its purpose is to be integrated into other classes that also use logger, primarily based on
[`attrsx`](https://kiril-mordan.github.io/reusables/attrsx/),
including support for injecting any initialized logger.
"""

import logging
import inspect
from typing import List, Dict, Any, Optional, Type, Callable
from datetime import datetime
import threading
import asyncio
import json
import os
import contextvars
import itertools
from functools import reduce
from operator import attrgetter
from pydantic import BaseModel, Field, SkipValidation
import dill #>=0.3.7
import attrs
import attrsx

from .components.shouterlog.asyncio_patch import patch_asyncio_proc_naming
from .components.shouterlog.log_plotter import LogPlotter
from .components.shouterlog.langfuse_handler import LangfuseHandler

_MISSING = object()
_LOG_ID_COUNTER = itertools.count(1)
_TRACEBACK_CTX = contextvars.ContextVar("shouter_last_traceback", default=[])
_LAST_TASK_CTX = contextvars.ContextVar("shouter_last_task_name", default=None)


__design_choices__ = {
    'logger' : ['shouter builds on standard logging so existing logger behavior is preserved',
                'attrsx logger chaining allows supplying any initialized logging.Logger instance',
                'only standard log methods are exposed (info/debug/warning/error/critical/fatal)'],
    '_format_mess' : ['_format_mess implements all predefined output formats (lines, headers, titles, warnings)',
                      '_format_mess triggers _select_output_type when output_type is not provided',
                      'format-related parameters can be passed via class defaults or per-call kwargs'],
    '_select_output_type' : ['auto formatting chooses a style based on traceback depth when output_type is None',
                             'manual formatting overrides auto selection by passing output_type explicitly'],
    'supported_classes' : ['supported_classes lists classes that should appear in readable tracebacks',
                           'when empty, shouter falls back to the immediate caller frame',
                           'including all participating classes improves traceback clarity'],
    'debugging_capabilities' : ['log records (tears) always store structured metadata for each log call',
                                'save_vars can attach selected serializable locals to any log record',
                                'error/critical/fatal can persist tears and an optional env snapshot for post-mortem debugging'],
    'persist_state' : ['persist state happens automatically for logger levels: error, critical, fatal',
                       'persist_state can be triggered manually to dump tears and optional env snapshot',
                       'tears are saved as JSON lines; env snapshot is saved with dill when persist_env=True'],
    'traceback_of_asyncio' : ['asyncio tasks have incomplete stacks; Proc-* tasks inherit parents via context',
                              'custom task names are appended to tracebacks for readability',
                              'logging before and after proc tasks helps maintain a coherent chain'],
    'actions' : ['actions are post-log hooks defined by LogAction and executed after a log call',
                 'actions can validate/prepare inputs and use the current log record (tear)',
                 'built-ins (e.g., Langfuse) are registered via add_actions() once initialized'],
    'plotting' : ['LogPlotter can render sequence diagrams from recorded tracebacks',
                  'show_sequence_diagram initializes the plotter lazily and uses log_records as input']
}


# Metadata for package creation
__package_metadata__ = {
    "author": "Kyrylo Mordan",
    "author_email": "parachute.repo@gmail.com",
    "description": "A custom logging tool that expands normal logger with additional formatting and debug capabilities.",
    "keywords" : ['python', 'logging', 'debug tool']
}


patch_asyncio_proc_naming()

class LogAction(BaseModel):

    """
    Action available from logger
    """

    name : str = Field(
        description = "Name of the function, that will be referenced in action params."
    )
    func: SkipValidation[Callable[..., Any]] = Field(
        description = "Sync function that has same inputs as input_model and performs some action based on them."
    )
    input_prep_func : SkipValidation[Callable[..., Any]] = Field(
        default=None,
        description = "Optional input preprocessing function that combines inputs with log traces."
    )
    input_model: Optional[Type[BaseModel]] = Field(
        default=None,
        description = "Optional input model for function, if cannot be derived from func definition."
    )
    
    model_config = {
        "arbitrary_types_allowed": True
    }

@attrsx.define(
    handler_specs = {
        "log_plotter" : LogPlotter,
        "langfuse" : LangfuseHandler},
    logger_chaining = {
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
    available_actions = attrs.field(default=[], type = List[LogAction])
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

        return out_mess, tear


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
                        name : str,
                        tear : Optional[dict] = None,
                        params : Optional[dict] = None):

    
        actions = [action for action in self.available_actions if action.name == name]

        if actions:

            if params is None:
                params = {}

            action = actions[0]

            input_params = {}
            if action.input_prep_func:
                inputs = action.input_prep_func( 
                    params=params,
                    log_item=tear)
                input_params = inputs.model_dump()
            else:
                if action.input_model:
                    inputs = action.input_model(**params)
                    input_params = inputs.model_dump()

            action.func(
                **input_params
            )


    def _log(self, 
             method, 
             mess : str = None,
             label : str = None,
             save_vars : list = None,
             dotline_length : int = None,
             output_type : str = None,
             auto_output_type_selection : bool = None,
             actions : list = None,
             logger : logging.Logger = None,
             *args, **kwargs):

        if dotline_length is None:
            dotline_length = self.dotline_length

        if auto_output_type_selection is None:
            auto_output_type_selection = self.auto_output_type_selection

        if logger is None:
            logger = self.logger

        formated_mess, tear = self._format_mess(mess = mess,
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

        if actions:

            [self._perform_action(name = action["name"],
                tear = tear, 
                params = action.get("params")) \
                for action in actions if action.get("name")]


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


    def add_actions(self, actions : List[LogAction] = None):

        """
        Updates list of available actions.
        """

        if actions is None:
            actions = []

        if self.langfuse_h:
            self.available_actions += [
                LogAction(
                    name = "langfuse.log_trace",
                    func = self.langfuse_h.log_trace,
                    input_model = self.langfuse_h.input_model,
                    input_prep_func = self.langfuse_h._prepare_inputs
                ),
                LogAction(
                    name = "langfuse.flush",
                    func = self.langfuse_h.flush,
                    input_model = None
                ),
            ]

        self.available_actions += actions



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
             actions : list = None,
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
            actions = actions,
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
             actions : list = None,
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
            actions = actions,
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
             actions : list = None,
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
            actions = actions,
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
             actions : list = None,
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
            actions = actions,
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
             actions : list = None,
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
            actions = actions,
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
             actions : list = None,
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
            actions = actions,
            logger = logger,
            *args, **kwargs
        )
