```python
import attrsx
import attrs
```

## Usage

### 1. Built-in logger

One of the primary extensions in `attrsx` is automatic logging. It can be accessed via `self.logger` in any `attrsx`-decorated class.

#### Basic Logger Usage


```python
@attrsx.define
class ProcessData:
    data: str = attrs.field(default=None)

    def run(self):
        self.logger.info("Running data processing...")
        self.logger.debug(f"Processing data: {self.data}")
        return f"Processed: {self.data}"

```


```python
ProcessData(data = "data").run()
```

    INFO:ProcessData:Running data processing...





    'Processed: data'



#### Logger Configuration

The logging behavior can be customized using the following optional attributes:

- `loggerLvl` : Sets the log level (from `logging`), defaults to `logging.INFO`.
- `logger_name` : Specifies the logger name; defaults to the class name.
- `logger_format` : Sets the logging message format, defaults to `%(levelname)s:%(name)s:%(message)s`.

`self.logger` becomes available starting from `__attrs_post_init__`.


```python
import logging

@attrsx.define
class VerboseProcess:
    data: str = attrs.field(default=None)
    loggerLvl: int = attrs.field(default=logging.DEBUG)
    logger_format: str = attrs.field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    def __attrs_post_init__(self):
        self.logger.info("Custom post-init logic")
        self.data = "DATA"

    def run(self):
        self.logger.debug(f"Processing {self.data}")
        self.logger.debug(dline=True)
        return f"Processed: {self.data}"

```


```python
VerboseProcess(data = "data").run()
```

    2025-12-29 20:36:10,019 - VerboseProcess - INFO - Custom post-init logic
    2025-12-29 20:36:10,020 - VerboseProcess - DEBUG - Processing DATA
    2025-12-29 20:36:10,020 - VerboseProcess - DEBUG - 





    'Processed: DATA'



#### Using External Loggers

Non standard loggers can enable additional functionality and normally ignored inputs that would not break normal logger, when attrsx is used.


```python
@attrsx.define
class ExtraLogger:

    def info(self, msg):
        self.logger.info(msg)

    def debug(self, msg = None, dline = False, *args, **kwargs):
        if dline is True:
            msg = "=" * 50
        self.logger.debug(msg, *args, **kwargs)

```

An external, pre-initialized logger can also be provided to the class using the `logger` attribute.


```python
extra_logger = ExtraLogger(loggerLvl=logging.DEBUG)

VerboseProcess(
    data = "data",
    logger = extra_logger
).run()
```

    INFO:ExtraLogger:Custom post-init logic
    DEBUG:ExtraLogger:Processing DATA
    DEBUG:ExtraLogger:==================================================





    'Processed: DATA'



### 2. Built-in handlers

Another extension in `attrsx` is `built-in handlers`. This feature is meant to help plug interchangeable helper objects (“handlers”) into a host class declaratively, without manual wiring, in a way that allows for both providing initialized handlers as well as initializing handlers within a class. 

The main class has access to methods of handler classes, can reinitialize them or reset them in a well defined way, where most additional code is added automatically by the library to the class.


#### Adding handlers to a class

To add handlers to an `attrsx` class, one can take advantage of `handler_specs` parameter within `@attrsx.define`, which takes a dictionary, where key is alias for the handler and value is the handler class.


```python
@attrsx.define(handler_specs={"procd": ProcessData})
class Service:
    def run(self, data: str):
        self.logger.info("Calling procd handler")
        self._initialize_procd_h(uparams={"data": data})
        return self.procd_h.run()

```


```python
Service().run("some data")
```

    INFO:Service:Calling procd handler
    INFO:ProcessData:Running data processing...





    'Processed: some data'



For each handler in provided via `handler_specs` in definition of `NewClass` as :

```python
@attrsx.define(handler_specs = {
    'handler_alias' : HandlerClass, ..., 
    'another_handler_alias_n' : AnotherHandlerClass})
class NewClass:
    ...
```

the class gets the following attributes:

- `{handler_alias}_h` : an instance of the handler, by default set to `None`
- `{handler_alias}_class` : a class of the handler, will be used if corresponding instance is None, when initialized
- `{handler_alias}_params` : parameters that should be used for creating new instance of the handler, using handler class

and a function:

```python
def _initialize_{handler_alias}_h(self, params : dict = None, uparams : dict = None):

    if params is None:
        params = self.{handler_alias}_params

    if uparams is not None:
        params.update(uparams)

    if self.{handler_alias}_h is None:
        self.{handler_alias}_h = self.{handler_alias}_class(**params)
```

which checks is initialized instance was already provided and if not, initializes handler with provided parameters.

To achieve the same with regular `attrs`, the `NewClass` could be defined in the following way, which would work exactly the same:

<details>

```python
@attrs.define
class NewClass:
    ...

    handler_alias_h = attrs.field(default=None)
    handler_alias_class = attrs.field(default=HandlerClass)
    handler_alias_params = attrs.field(default={})

    another_handler_alias_n_h = attrs.field(default=None)
    another_handler_alias_n_class = attrs.field(default=AnotherHandlerClass)
    another_handler_alias_n_params = attrs.field(default={})

    logger_chaining = attrs.field(default={
        'loggerLvl' : True, 
        'logger' : False, 
        'logger_format' : True})

    def _apply_logger_chaining(self, handler_class, params):

        if self.logger_chaining.get("logger"):
            if ('logger' in handler_class.__dict__) \
                    and "logger" not in params.keys():
                params["logger"] = self.logger

        if self.logger_chaining.get("loggerLvl"):

            if ('loggerLvl' in handler_class.__dict__) \
                    and "loggerLvl" not in params.keys():
                params["loggerLvl"] = self.loggerLvl

        if self.logger_chaining.get("logger_format"):

            if ('logger_format' in handler_class.__dict__) \
                    and "logger_format" not in params.keys():
                params["logger_format"] = self.logger_format

        return params

    def _initialize_handler_alias_h(self, params : dict = None, uparams : dict = None):

        if params is None:
            params = self.handler_alias_params

        if uparams is not None:
            params.update(uparams)

        params = self._apply_logger_chaining(
            handler_class = self.handler_alias_class, 
            params = params)

        if self.handler_alias_h is None:
            self.handler_alias_n_h = self.handler_alias_class(**params)

    def _initialize_another_handler_alias_n_h(self, params : dict = None, uparams : dict = None):

        if params is None:
            params = self.another_handler_alias_n_params

        if uparams is not None:
            params.update(uparams)

        params = self._apply_logger_chaining(
            handler_class = self.another_handler_alias_n_class, 
            params = params)

        if self.another_handler_alias_n_h is None:
            self.another_handler_alias_n_h = self.another_handler_alias_n_class(**params)
    
```

</details>

#### Setting default parameters

For each handler there is `{handler_alias}_params` within new class, which can be used to provide parameters for handler initialization. 

Sometimes there is a need to extend or update default parameters and initialize/reinitialize the handler. Each handler has `_initialize_{handler_alias}_h` method within new class to which new default params (parameters that one would use when initializing handler class) could be passed via `params` and update to these or `{handler_alias}_params` via `uparams`.


```python
@attrsx.define(handler_specs = {'procd' : ProcessData})
class Service:
    data: str = attrs.field(default=None)

    procd_params = attrs.field(default={"loggerLvl" : logging.DEBUG})

    def run(self, data : str):

        self.logger.info("Running method from procd handler!")

        self._initialize_procd_h(uparams={"data" : data})

        return self.procd_h.run()

```


```python
Service().run(data = "some data")

```

    INFO:Service:Running method from procd handler!
    INFO:ProcessData:Running data processing...
    DEBUG:ProcessData:Processing data: some data





    'Processed: some data'



#### Adding handler initialization to class post init

One of the benefits of using `attrs` is the ability to define what happens when class in initialized without making the whole `__init__`, by using `__attrs_post_init__`. Some handlers could be added there to be initialized with a new class and rdy to be used within its methods. 


```python
@attrsx.define(handler_specs = {'procd' : ProcessData})
class Service:
    data: str = attrs.field(default=None)

    procd_params = attrs.field(default={"data" : "default data"})

    def __attrs_post_init__(self):
        self._initialize_procd_h()

    def run(self, data : str = None):

        self.logger.info("Running method from procd handler!")

        return self.procd_h.run()
```


```python
Service().run()
```

    INFO:Service:Running method from procd handler!
    INFO:ProcessData:Running data processing...





    'Processed: default data'



#### Using instances of handlers initialized outside of new class

Each new class defined with `handler_specs` can use initialized instances of handlers and skip initialization within new class, which allows the code to remain flexible. 


```python
@attrsx.define(handler_specs = {'procd' : ProcessData})
class Service:
    data: str = attrs.field(default=None)

    procd_params = attrs.field(default={"data" : "default data"})

    def __attrs_post_init__(self):
        self._initialize_procd_h()

    def run(self, data : str = None):

        self.logger.info("Running method from procd handler!")

        return self.procd_h.run()
```


```python
outside_procd = ProcessData(data = 'some other data')

Service(procd_h=outside_procd).run()
```

    INFO:Service:Running method from procd handler!
    INFO:ProcessData:Running data processing...





    'Processed: some other data'



#### Chaining loggers

Each `attrsx` class has its own independent built-in logger, it might be useful to control behaviour of handler loggers from main class (for handlers that themselves are `attrsx` classes). This package allows to chain loggers of `attrsx` classes on 3 different levels via `logger_chaining` boolean parameters in `@attrsx.define`:

1. `logger_format` : synchronizes logger format for all `attrsx` handlers (by default set to `True`)
2. `loggerLvl` : synchronizes logger level for all `attrsx` handlers (by default set to `True`)
3. `logger` : uses logger defined for main class within handlers (by default set to `False`)


```python
@attrsx.define(handler_specs = {'procd' : ProcessData})
class ChainedService:
    data: str = attrs.field(default=None)

    procd_params = attrs.field(default={"data" : "default data"})

    loggerLvl = attrs.field(default=logging.DEBUG)
    logger_format = attrs.field(default="%(levelname)s - %(name)s - %(message)s")

    def __attrs_post_init__(self):
        self._initialize_procd_h()

    def run(self, data : str = None):

        self.logger.info("Running method from procd handler!")

        return self.procd_h.run()
```


```python
ChainedService().run()
```

    INFO - ChainedService - Running method from procd handler!
    INFO - ProcessData - Running data processing...
    DEBUG - ProcessData - Processing data: default data





    'Processed: default data'




```python
@attrsx.define(handler_specs = {'procd' : ProcessData}, logger_chaining={'logger' : True})
class ChainedService:
    data: str = attrs.field(default=None)

    procd_params = attrs.field(default={"data" : "default data"})

    loggerLvl = attrs.field(default=logging.DEBUG)
    logger_format = attrs.field(default="%(levelname)s - %(name)s - %(message)s")

    def __attrs_post_init__(self):
        self._initialize_procd_h()

    def run(self, data : str = None):

        self.logger.info("Running method from procd handler!")

        return self.procd_h.run()
```


```python
ChainedService().run()
```

    INFO - ChainedService - Running method from procd handler!
    INFO - ChainedService - Running data processing...
    DEBUG - ChainedService - Processing data: default data





    'Processed: default data'


