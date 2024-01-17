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
2. basic usage like logging
3. using different output types
4. custom logger configuration
5. backwards compatibility with existing loggers
6. built-in records from Shouter usage
7. debugging capabilities of Shouter

### 1. Initialize Shouter Class


```python
shouter = Shouter(
    # optional/ required
    supported_classes = (),
    # optionally 
    ## Formatting settings
    dotline_length = 50,
    auto_output_type_selection = True,
    # For saving records
    tears_persist_path = '../env_spec/log_records.json',
    datetime_format = "%Y-%m-%d %H:%M:%S",
    # For saving env
    persist_env = False,
    env_persist_path = '../env_spec/environment.dill',
    ## Logger settings
    logger = None,
    logger_name = 'Shouter',
    loggerLvl = logging.DEBUG,
    logger_format = '(%(asctime)s) : %(name)s : [%(levelname)s] : %(message)s'
)

```

### 2. Basic usage like logging


```python
shouter.debug(
    # optional
    dotline_length=30)
shouter.debug("This is a debug message!")
shouter.info("This is an info message!")
shouter.warning("This is a warning message!")
shouter.error("This is an error message!")
shouter.fatal("This is a fatal message!")
shouter.critical("This is a critical message!")
```

    (2024-01-17 17:17:35,565) : Shouter : [DEBUG] : ==============================


    (2024-01-17 17:17:35,566) : Shouter : [DEBUG] : This is a debug message!


    (2024-01-17 17:17:35,567) : Shouter : [INFO] : This is an info message!


    (2024-01-17 17:17:35,568) : Shouter : [WARNING] : This is a warning message!


    (2024-01-17 17:17:35,569) : Shouter : [ERROR] : This is an error message!


    (2024-01-17 17:17:35,571) : Shouter : [CRITICAL] : This is a fatal message!


    (2024-01-17 17:17:35,571) : Shouter : [CRITICAL] : This is a critical message!


### 3. Using different output types


```python
# Different types of outputs
shouter.info(output_type="dline")
shouter.info(output_type="HEAD1", mess="Header Message")
```

    (2024-01-17 17:17:35,612) : Shouter : [INFO] : ==================================================


    (2024-01-17 17:17:35,612) : Shouter : [INFO] : 
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
shouter_with_custom_logger = Shouter(supported_classes=(), logger=custom_logger)
shouter_with_custom_logger.info(mess="Message with custom logger")
```

    (2024-01-17 17:17:35,619) : CustomLogger : [INFO] : Message with custom logger


### 5. Backwards compatibility with existing loggers


```python
import logging
import attr #>=22.2.0


@attr.s
class ExampleClass:

    # Logger settings
    logger = attr.ib(default=None)
    logger_name = attr.ib(default='Example Class')
    loggerLvl = attr.ib(default=logging.DEBUG)
    logger_format = attr.ib(default='(%(asctime)s) : %(name)s : [%(levelname)s] : %(message)s')

    def __attrs_post_init__(self):
        self.initialize_logger()

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
            
    def print_debug(self):
        
        self.logger.debug("This is a debug message!")
        
    def print_info(self):
        
        self.logger.info("This is a info message!")
        
    def print_warning(self):
        
        self.logger.warning("This is a warning message!")
        
    def print_error(self):
        
        self.logger.error("This is a error message!")
        
    def print_critical(self):
        
        self.logger.critical("This is a critical message!")
        
    def perform_action_chain_1(self):
        
        self.logger.debug("Action 1")
        self.print_debug()
                
        self.logger.debug("Action 2")
        self.print_error()
        
    def perform_action_chain_2(self):
                
        a = 1
        b = 'b'
        c = ['list']
        d = {'key' : 'value'}
        e = Shouter()
        
        self.logger.error("Saving env")
```


```python
ec = ExampleClass()

ec.print_debug()
ec.print_info()
ec.print_warning()
ec.print_error()
ec.print_critical()
```

    (2024-01-17 17:17:35,635) : Example Class : [DEBUG] : This is a debug message!


    (2024-01-17 17:17:35,636) : Example Class : [INFO] : This is a info message!


    (2024-01-17 17:17:35,637) : Example Class : [WARNING] : This is a warning message!


    (2024-01-17 17:17:35,638) : Example Class : [ERROR] : This is a error message!


    (2024-01-17 17:17:35,639) : Example Class : [CRITICAL] : This is a critical message!



```python
shouter_for_example_class = Shouter(
    supported_classes = (ExampleClass),
    tears_persist_path = '../env_spec/log_records.json'
    )

ec = ExampleClass(logger=shouter_for_example_class)

ec.print_debug()
ec.print_info()
ec.print_warning()
ec.print_error()
ec.print_critical()
ec.perform_action_chain_1()
```

    (2024-01-17 17:17:35,645) : Shouter : [DEBUG] : This is a debug message!


    (2024-01-17 17:17:35,646) : Shouter : [INFO] : This is a info message!


    (2024-01-17 17:17:35,646) : Shouter : [WARNING] : This is a warning message!


    (2024-01-17 17:17:35,647) : Shouter : [ERROR] : This is a error message!


    (2024-01-17 17:17:35,648) : Shouter : [CRITICAL] : This is a critical message!


    (2024-01-17 17:17:35,649) : Shouter : [DEBUG] : Action 1


    (2024-01-17 17:17:35,649) : Shouter : [DEBUG] : + This is a debug message!


    (2024-01-17 17:17:35,650) : Shouter : [DEBUG] : Action 2


    (2024-01-17 17:17:35,650) : Shouter : [ERROR] : + This is a error message!


### 6. Built-in records from Shouter usage


```python
shouter_for_example_class = Shouter(
    supported_classes = (ExampleClass),
    tears_persist_path = '../env_spec/log_records.json'
    )

ec = ExampleClass(logger=shouter_for_example_class)

ec.print_debug()
ec.perform_action_chain_1()
```

    (2024-01-17 17:17:35,657) : Shouter : [DEBUG] : This is a debug message!


    (2024-01-17 17:17:35,658) : Shouter : [DEBUG] : Action 1


    (2024-01-17 17:17:35,659) : Shouter : [DEBUG] : + This is a debug message!


    (2024-01-17 17:17:35,659) : Shouter : [DEBUG] : Action 2


    (2024-01-17 17:17:35,660) : Shouter : [ERROR] : + This is a error message!



```python
ec.logger.return_logged_tears()
```




    [{'datetime': '2024-01-17 17:17:35',
      'level': 'debug',
      'function': 'ExampleClass.print_debug',
      'mess': 'This is a debug message!',
      'line': 33,
      'lines': [33],
      'traceback': ['ExampleClass.print_debug']},
     {'datetime': '2024-01-17 17:17:35',
      'level': 'debug',
      'function': 'ExampleClass.perform_action_chain_1',
      'mess': 'Action 1',
      'line': 53,
      'lines': [53],
      'traceback': ['ExampleClass.perform_action_chain_1']},
     {'datetime': '2024-01-17 17:17:35',
      'level': 'debug',
      'function': 'ExampleClass.perform_action_chain_1',
      'mess': 'This is a debug message!',
      'line': 54,
      'lines': [33, 54],
      'traceback': ['ExampleClass.print_debug',
       'ExampleClass.perform_action_chain_1']},
     {'datetime': '2024-01-17 17:17:35',
      'level': 'debug',
      'function': 'ExampleClass.perform_action_chain_1',
      'mess': 'Action 2',
      'line': 56,
      'lines': [56],
      'traceback': ['ExampleClass.perform_action_chain_1']},
     {'datetime': '2024-01-17 17:17:35',
      'level': 'error',
      'function': 'ExampleClass.perform_action_chain_1',
      'mess': 'This is a error message!',
      'line': 57,
      'lines': [45, 57],
      'traceback': ['ExampleClass.print_error',
       'ExampleClass.perform_action_chain_1']}]




```python
import pandas as pd

pd.DataFrame(ec.logger.return_logged_tears())
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>datetime</th>
      <th>level</th>
      <th>function</th>
      <th>mess</th>
      <th>line</th>
      <th>lines</th>
      <th>traceback</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>2024-01-17 17:17:35</td>
      <td>debug</td>
      <td>ExampleClass.print_debug</td>
      <td>This is a debug message!</td>
      <td>33</td>
      <td>[33]</td>
      <td>[ExampleClass.print_debug]</td>
    </tr>
    <tr>
      <th>1</th>
      <td>2024-01-17 17:17:35</td>
      <td>debug</td>
      <td>ExampleClass.perform_action_chain_1</td>
      <td>Action 1</td>
      <td>53</td>
      <td>[53]</td>
      <td>[ExampleClass.perform_action_chain_1]</td>
    </tr>
    <tr>
      <th>2</th>
      <td>2024-01-17 17:17:35</td>
      <td>debug</td>
      <td>ExampleClass.perform_action_chain_1</td>
      <td>This is a debug message!</td>
      <td>54</td>
      <td>[33, 54]</td>
      <td>[ExampleClass.print_debug, ExampleClass.perfor...</td>
    </tr>
    <tr>
      <th>3</th>
      <td>2024-01-17 17:17:35</td>
      <td>debug</td>
      <td>ExampleClass.perform_action_chain_1</td>
      <td>Action 2</td>
      <td>56</td>
      <td>[56]</td>
      <td>[ExampleClass.perform_action_chain_1]</td>
    </tr>
    <tr>
      <th>4</th>
      <td>2024-01-17 17:17:35</td>
      <td>error</td>
      <td>ExampleClass.perform_action_chain_1</td>
      <td>This is a error message!</td>
      <td>57</td>
      <td>[45, 57]</td>
      <td>[ExampleClass.print_error, ExampleClass.perfor...</td>
    </tr>
  </tbody>
</table>
</div>



### 7. Debugging capabilities of Shouter


```python
shouter_for_example_class = Shouter(
    supported_classes = (ExampleClass),
    tears_persist_path = '../env_spec/log_records.json',
    persist_env = True,
    env_persist_path = '../env_spec/environment.dill'
)

ec = ExampleClass(logger=shouter_for_example_class)

ec.print_debug()
ec.perform_action_chain_2()
```

    (2024-01-17 17:17:35,926) : Shouter : [DEBUG] : This is a debug message!


    (2024-01-17 17:17:35,926) : Shouter : [ERROR] : Saving env


    (2024-01-17 17:17:35,959) : Shouter : [WARNING] : Object 'self' could not have been serialized, when saving last words!



```python
ec.logger.return_last_words(
    # optional
    env_persist_path = '../env_spec/environment.dill'
)
```




    {'a': 1,
     'b': 'b',
     'c': ['list'],
     'd': {'key': 'value'},
     'e': Shouter(supported_classes=(), dotline_length=50, auto_output_type_selection=True, tears_persist_path='log_records.json', env_persist_path='environment.dill', datetime_format='%Y-%m-%d %H:%M:%S', log_records=[], persist_env=False, logger=<Logger Shouter (DEBUG)>, logger_name='Shouter', loggerLvl=10, logger_format='(%(asctime)s) : %(name)s : [%(levelname)s] : %(message)s')}


