# Shouter Usage Examples

The Shouter class is designed for managing and displaying formatted log messages, utilizing Python's logging module. 



```python
import sys
sys.path.append('../')
from python_modules.shouter import Shouter
# optional
import logging
```

## Usage examples

The examples contain: 
1. initialize Shouter class
2. basic usage of shout method
3. using different output types
4. custom logger configuration

### 1. Initialize Shouter Class


```python
shouter = Shouter(
    # optionally 
    ## Formatting settings
    dotline_length = 50,
    ## Logger settings
    logger = None,
    logger_name = 'Shouter',
    loggerLvl = logging.DEBUG,
    logger_format = '(%(asctime)s) : %(name)s : [%(levelname)s] : %(message)s'
)

```

### 2. Basic usage of shout method


```python
# Simple shout with default settings
shouter.shout()

# Shout with a custom message and line length
shouter.shout(mess="Custom Message", dotline_length=30)

```

    (2023-12-10 00:21:17,154) : Shouter : [INFO] : ==================================================
    (2023-12-10 00:21:17,155) : Shouter : [INFO] : *** Custom Message


### 3. Using different output types


```python
# Different types of outputs
shouter.shout(output_type="dline")
shouter.shout(output_type="HEAD1", mess="Header Message")
```

    (2023-12-10 00:21:17,197) : Shouter : [INFO] : ==================================================
    (2023-12-10 00:21:17,198) : Shouter : [INFO] : 
    ==================================================
    -----------------Header Message----------------- 
    ==================================================


### 4. Custom logger configuration


```python
import logging

# Custom logger
custom_logger = logging.getLogger("CustomLogger")
custom_logger.setLevel(logging.INFO)

# Shouter with custom logger
shouter_with_custom_logger = Shouter(logger=custom_logger)
shouter_with_custom_logger.shout(mess="Message with custom logger")
```

    (2023-12-10 00:21:17,204) : CustomLogger : [INFO] : *** Message with custom logger

