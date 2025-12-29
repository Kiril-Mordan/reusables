"""
**attrsx – An Extension to _attrs_ for Declarative Handler Injection & Integrated Logging**

---

### 1. Purpose

`attrsx` builds on top of the `attrs` data‑class library and contributes two orthogonal capabilities that are frequently needed in service‑layer and infrastructure code:

1. **Integrated Logging** – transparent, boilerplate‑free creation of a configured `logging.Logger` for every instance.
2. **Declarative Handler Injection** – generation of lazy‑initialised *strategy* objects (“handlers”) declared via `handler_specs`.

Both features are opt‑in; if a class does not request them, `attrsx.define` behaves exactly like `attrs.define`.

---

### 2. Key Features

* **Drop-in replacement for `attrs.define`** – forwards every keyword parameter that `attrs.define` understands (`slots`, `frozen`, `kw_only`, validators, converters, …).

* **Integrated logging** – injects four fields (`logger`, `loggerLvl`, `logger_name`, `logger_format`) and wraps `__attrs_post_init__` to attaches a `logging.logger` 
    to the instance if none is present.  The logger’s name defaults to the class name; level and format are configurable per instance.

* **Declarative handler injection** – for each entry in `handler_specs={"key": HandlerClass, ...}` the decorator adds three fields  
  (`<key>_class`, `<key>_params`, `<key>_h`) plus a lazy factory method `_initialize_<key>_h()`, which calls  
  `<key>_class(**<key>_params)` the first time it is invoked.

* **Type-hint compliance** – all generated attributes are inserted into `__annotations__`, so static type-checkers recognise them.

* **Zero runtime overhead** – field and method generation is performed once, at import time; normal instance construction stays on the `attrs` fast path.


---

### 3. Underlying Pattern

The handler mechanism realises **Declarative Handler Injection** (a variant of the Strategy pattern implemented through composition and a lazy factory method). 
Configuration is expressed as data, leaving the host class agnostic of concrete strategy classes.

---

### 4. When to Use

- You need consistent, ready‑to‑use logging across many small classes.
- You want to supply interchangeable helper or strategy objects without manual glue code.
- You prefer composition over inheritance but dislike factory boilerplate.

If none of the above apply, simply continue to use `attrs.define`; the migration path is one import statement.


"""

import logging
import attrs #>=22.2.0



__package_metadata__ = {
    "author": "Kyrylo Mordan",
    "author_email": "parachute.repo@gmail.com",
    "description": "A lightweight extension of attrs that adds extras like logging.",
    'license' : 'mit',
    "url" : 'https://kiril-mordan.github.io/reusables/attrsx/'
}

_STD_LOG_KWARGS = {"exc_info", "stack_info", "stacklevel", "extra"}


class _LoggerKwargFilter:
    """
    Wraps a logger so that extra kwargs are:
    - passed through if logger declares __log_kwargs__
    - silently dropped otherwise
    """

    def __init__(self, logger):
        if isinstance(logger, _LoggerKwargFilter):
            logger = logger._logger
        self._logger = logger
        self._extra = getattr(logger, "__log_kwargs__", None)

    
    def __getstate__(self):
        return {"_logger": self._logger}

    def __setstate__(self, state):
        self._logger = state["_logger"]
        self._extra = getattr(self._logger, "__log_kwargs__", None)

    def _filter(self, kwargs):
        if not kwargs:
            return kwargs

        if self._extra is None:
            # standard logger → keep only standard logging kwargs
            return {k: v for k, v in kwargs.items() if k in _STD_LOG_KWARGS}

        allowed = _STD_LOG_KWARGS | set(self._extra)
        return {k: v for k, v in kwargs.items() if k in allowed}

    def debug(self, msg = None, *args, **kwargs):
        if msg is None:
            msg = ""
        return self._logger.debug(msg, *args, **self._filter(kwargs))

    def info(self, msg = None, *args, **kwargs):
        if msg is None:
            msg = ""
        return self._logger.info(msg, *args, **self._filter(kwargs))

    def warning(self, msg = None, *args, **kwargs):
        if msg is None:
            msg = ""
        return self._logger.warning(msg, *args, **self._filter(kwargs))

    def error(self, msg = None, *args, **kwargs):
        if msg is None:
            msg = ""
        return self._logger.error(msg, *args, **self._filter(kwargs))

    def critical(self, msg = None, *args, **kwargs):
        if msg is None:
            msg = ""
        return self._logger.critical(msg, *args, **self._filter(kwargs))

    def fatal(self, msg = None, *args, **kwargs):
        if msg is None:
            msg = ""
        return self._logger.fatal(msg, *args, **self._filter(kwargs))

    def exception(self, msg = None, *args, **kwargs):
        if msg is None:
            msg = ""
        return self._logger.exception(msg, *args, **self._filter(kwargs))

    def __getattr__(self, name):
        return getattr(self._logger, name)

def define(
    cls=None, 
    handler_specs:dict=None, 
    logger_chaining:dict=None, 
    *args, **kwargs):
    if cls is not None:
        return _apply_attrs_and_logger(
            cls = cls, 
            handler_specs = handler_specs, 
            logger_chaining = logger_chaining,
            *args, **kwargs)
    
    def wrapper(inner_cls):
        return _apply_attrs_and_logger(
            cls = inner_cls, 
            handler_specs = handler_specs, 
            logger_chaining = logger_chaining, 
            *args, **kwargs)
    
    return wrapper

def _unwrap_logger(logger):
    # unwrap repeatedly if already wrapped
    while isinstance(logger, _LoggerKwargFilter):
        logger = logger._logger
    return logger


def _add_handlers_from_spec(cls, handler_specs : dict, logger_chaining: dict):

    if logger_chaining is None:
        logger_chaining = {}

    logger_chaining_default = {
        'loggerLvl' : True, 
        'logger' : False, 
        'logger_format' : True}
    logger_chaining_default.update(logger_chaining)
    logger_chaining = logger_chaining_default

    for handler_key, handler_class in handler_specs.items():

        handler_h_name = f"{handler_key}_h"
        handler_class_name = f"{handler_key}_class"
        handler_params_name = f"{handler_key}_params"

        if handler_h_name not in cls.__dict__:
            setattr(cls, handler_h_name, attrs.field(default=None))
        if handler_class_name not in cls.__dict__:
            setattr(cls, handler_class_name, attrs.field(default=handler_class))
        if handler_params_name not in cls.__dict__:
            setattr(cls, handler_params_name, attrs.field(factory=dict))

        init_func = f"""
def _initialize_{handler_h_name}(self, params : dict = None, uparams : dict = None):

    if params is None:
        params = self.{handler_params_name}
    
    params = dict(params) if params is not None else {{}}

    if uparams is not None:
        params.update(uparams)
    """

        if logger_chaining.get("logger"):
            init_func += f"""
    if ('logger' in self.{handler_class_name}.__dict__) \
            and "logger" not in params.keys():
        params["logger"] = self.logger
    """
        if logger_chaining.get("loggerLvl"):
            init_func += f"""
    if ('loggerLvl' in self.{handler_class_name}.__dict__) \
            and "loggerLvl" not in params.keys():
        params["loggerLvl"] = self.loggerLvl
    """
        if logger_chaining.get("logger_format"):
            init_func += f"""
    if ('logger_format' in self.{handler_class_name}.__dict__) \
            and "logger_format" not in params.keys():
        params["logger_format"] = self.logger_format
    """

        init_func += f"""
    if self.{handler_h_name} is None:
        self.{handler_h_name} = self.{handler_class_name}(**params)
        """

        ns = {}
        exec(init_func, ns)

        init_fn = ns[f'_initialize_{handler_h_name}']

        setattr(cls, f'_initialize_{handler_h_name}', init_fn)

    return cls

def _apply_attrs_and_logger(cls, handler_specs, logger_chaining, *args, **kwargs):

    # Inject optional handlers definition
    if handler_specs:
        cls = _add_handlers_from_spec(
            cls = cls, 
            handler_specs=handler_specs, 
            logger_chaining = logger_chaining)

    # Inject logger fields ONLY if they don't already exist
    if 'logger' not in cls.__dict__:
        cls.logger = attrs.field(default = None, repr=False)
    if 'loggerLvl' not in cls.__dict__:
        cls.loggerLvl = attrs.field(default=logging.INFO)
    if 'logger_name' not in cls.__dict__:
        cls.logger_name = attrs.field(default=None)
    if 'logger_format' not in cls.__dict__:
        cls.logger_format = attrs.field(default="%(levelname)s:%(name)s:%(message)s")

    # Preserve existing __attrs_post_init__ if it exists
    original_post_init = getattr(cls, "__attrs_post_init__", None)

    # Define a wrapper __attrs_post_init__ to initialize the logger
    def __attrs_post_init__(self):
        # Logger setup (before custom post-init logic)
        if not hasattr(self, 'logger') or self.logger is None:

            raw_logger = logging.getLogger(self.logger_name or self.__class__.__name__)
            raw_logger.setLevel(self.loggerLvl)
            self.logger = _LoggerKwargFilter(raw_logger)

            # Clear existing handlers to avoid duplicates
            self.logger.handlers.clear()

            handler = logging.StreamHandler()
            formatter = logging.Formatter(self.logger_format)
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.propagate = False  # Prevent log duplication
    
        # Call the original post-init if it exists
        if original_post_init:
            original_post_init(self)

    # Attach the wrapped __attrs_post_init__ to the class
    cls.__attrs_post_init__ = __attrs_post_init__

    # Apply attrs.define
    return attrs.define(cls, *args, **kwargs)
