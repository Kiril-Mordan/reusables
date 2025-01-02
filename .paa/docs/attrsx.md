```python
import attrsx
import attrs
```

## Usage

### 1. Built-in logger

One of the primary extensions in `attrsx` is `automatic logging`. It can be accessed via `self.logger` in any `attrsx`-decorated class.

#### Example: Basic Logger Usage


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
- `logger_format` : Sets the logging message format; defaults to `%(levelname)s:%(name)s:%(message)s`.

`self.logger` becomes available starting from `__attrs_post_init__`.


```python
import logging

@attrsx.define
class ProcessData2:
    data: str = attrs.field(default=None)
    
    # optional attributes
    loggerLvl: int = attrs.field(default=logging.DEBUG) 
    logger_name : str = attrs.field(default="ProcessData")
    logger_format : str = attrs.field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    def __attrs_post_init__(self):
        self.logger.info("Custom post-init logic running!")
        self.data = "DATA"

    def run(self):
        self.logger.info("Running data processing...")
        self.logger.debug(f"Processing data: {self.data}")
        return f"Processed: {self.data}"
```


```python
ProcessData2(data = "data").run()
```

    2025-01-02 23:26:02,710 - ProcessData - INFO - Custom post-init logic running!
    2025-01-02 23:26:02,711 - ProcessData - INFO - Running data processing...
    2025-01-02 23:26:02,711 - ProcessData - DEBUG - Processing data: DATA





    'Processed: DATA'



#### Using External Loggers

An external, pre-initialized logger can also be provided to the class using the `logger` attribute.


```python
ProcessData2(
    data = "data",
    logger = ProcessData().logger
).run()
```

    INFO:ProcessData:Custom post-init logic running!
    INFO:ProcessData:Running data processing...





    'Processed: DATA'


