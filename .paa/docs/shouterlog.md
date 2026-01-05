```python
from shouterlog import Shouter
# optional
import logging
```

### 1. Initialize Shouter Class


```python
shouter = Shouter(
    # optional/ required
    supported_classes = (),
    # optionally 
    ## Formatting settings
    dotline_length = 50,
    auto_output_type_selection = True,
    show_function = True,
    show_traceback = False,
    # For saving records
    tears_persist_path = 'log_records.json',
    datetime_format = "%Y-%m-%d %H:%M:%S",
    # For saving env
    persist_env = False,
    env_persist_path = 'environment.dill',
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

    (2026-01-05 23:34:12,197) : Shouter : [DEBUG] : _format_mess:==============================
    (2026-01-05 23:34:12,199) : Shouter : [DEBUG] : _format_mess:This is a debug message!
    (2026-01-05 23:34:12,201) : Shouter : [INFO] : _format_mess:This is an info message!
    (2026-01-05 23:34:12,203) : Shouter : [WARNING] : _format_mess:This is a warning message!
    (2026-01-05 23:34:12,204) : Shouter : [ERROR] : _format_mess:This is an error message!
    (2026-01-05 23:34:12,206) : Shouter : [CRITICAL] : _format_mess:This is a fatal message!
    (2026-01-05 23:34:12,208) : Shouter : [CRITICAL] : _format_mess:This is a critical message!


### 3. Using different output types


```python
# Different types of outputs
shouter.info(output_type="dline")
shouter.info(output_type="HEAD1", mess="Header Message")
```

    (2026-01-05 23:34:12,214) : Shouter : [INFO] : _format_mess:==================================================
    (2026-01-05 23:34:12,216) : Shouter : [INFO] : _format_mess:
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

### 5. Backwards compatibility with existing loggers


```python
import logging
import attrsx

@attrsx.define
class ExampleClass:

            
    def print_debug(self):

        a = 0

        self.logger.debug("This is a debug message!", save_vars = ["a"])
        
    def print_info(self):
        
        self.logger.info("This is a info message!")
        
    def print_warning(self):
        
        self.logger.warning("This is a warning message!")
        
    def print_error(self):
        
        self.logger.error("This is a error message!", label = "TEST")
        
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
        
        self.logger.info("Logging vars", save_vars = ["a","b","e"])
        self.logger.error("Saving env", label = "TEST")
```


```python
ec = ExampleClass()

ec.print_debug()
ec.print_info()
ec.print_warning()
ec.print_error()
ec.print_critical()
```

    INFO:ExampleClass:This is a info message!
    WARNING:ExampleClass:This is a warning message!
    ERROR:ExampleClass:This is a error message!
    CRITICAL:ExampleClass:This is a critical message!



```python
shouter_for_example_class = Shouter(
    supported_classes = (ExampleClass,),
    tears_persist_path = 'log_records.json'
)

ec = ExampleClass(logger=shouter_for_example_class)

ec.print_debug()
ec.print_info()
ec.print_warning()
ec.print_error()
ec.print_critical()
ec.perform_action_chain_1()
```

    INFO:Shouter:ExampleClass.print_info:This is a info message!
    WARNING:Shouter:ExampleClass.print_warning:This is a warning message!
    ERROR:Shouter:ExampleClass.print_error:This is a error message!
    CRITICAL:Shouter:ExampleClass.print_critical:This is a critical message!
    ERROR:Shouter:ExampleClass.print_error:+ This is a error message!


### 6. Built-in records from Shouter usage


```python
shouter_for_example_class = Shouter(
    supported_classes = (ExampleClass,),
    tears_persist_path = 'log_records.json'
)

ec = ExampleClass(logger=shouter_for_example_class)

ec.print_debug()
ec.perform_action_chain_1()
```

    ERROR:Shouter:ExampleClass.print_error:+ This is a error message!



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
      <th>idx</th>
      <th>call_id</th>
      <th>datetime</th>
      <th>level</th>
      <th>function</th>
      <th>mess</th>
      <th>line</th>
      <th>lines</th>
      <th>is_proc</th>
      <th>proc_name</th>
      <th>traceback</th>
      <th>label</th>
      <th>env</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>1</td>
      <td>124165912314352</td>
      <td>2026-01-05 23:34:12</td>
      <td>debug</td>
      <td>ExampleClass.print_debug</td>
      <td>This is a debug message!</td>
      <td>12</td>
      <td>[12]</td>
      <td>False</td>
      <td>Task-2</td>
      <td>[ExampleClass.print_debug]</td>
      <td>None</td>
      <td>{'a': 0}</td>
    </tr>
    <tr>
      <th>1</th>
      <td>2</td>
      <td>124165917350880</td>
      <td>2026-01-05 23:34:12</td>
      <td>debug</td>
      <td>ExampleClass.perform_action_chain_1</td>
      <td>Action 1</td>
      <td>32</td>
      <td>[32]</td>
      <td>False</td>
      <td>Task-2</td>
      <td>[ExampleClass.perform_action_chain_1]</td>
      <td>None</td>
      <td>{}</td>
    </tr>
    <tr>
      <th>2</th>
      <td>3</td>
      <td>109462141702832</td>
      <td>2026-01-05 23:34:12</td>
      <td>debug</td>
      <td>ExampleClass.print_debug</td>
      <td>This is a debug message!</td>
      <td>12</td>
      <td>[12, 33]</td>
      <td>False</td>
      <td>Task-2</td>
      <td>[ExampleClass.print_debug, ExampleClass.perfor...</td>
      <td>None</td>
      <td>{'a': 0}</td>
    </tr>
    <tr>
      <th>3</th>
      <td>4</td>
      <td>124165917350880</td>
      <td>2026-01-05 23:34:12</td>
      <td>debug</td>
      <td>ExampleClass.perform_action_chain_1</td>
      <td>Action 2</td>
      <td>35</td>
      <td>[35]</td>
      <td>False</td>
      <td>Task-2</td>
      <td>[ExampleClass.perform_action_chain_1]</td>
      <td>None</td>
      <td>{}</td>
    </tr>
    <tr>
      <th>4</th>
      <td>5</td>
      <td>109462142051424</td>
      <td>2026-01-05 23:34:12</td>
      <td>error</td>
      <td>ExampleClass.print_error</td>
      <td>This is a error message!</td>
      <td>24</td>
      <td>[24, 36]</td>
      <td>False</td>
      <td>Task-2</td>
      <td>[ExampleClass.print_error, ExampleClass.perfor...</td>
      <td>TEST</td>
      <td>{}</td>
    </tr>
  </tbody>
</table>
</div>



### 7. Debugging errors with Shouter


```python
shouter_for_example_class = Shouter(
    supported_classes = (ExampleClass,),
    tears_persist_path = 'log_records.json',
    persist_env = True,
    env_persist_path = 'environment.dill'
)

ec = ExampleClass(logger=shouter_for_example_class)

ec.print_debug()
ec.perform_action_chain_2()
```

    INFO:Shouter:ExampleClass.perform_action_chain_2:Logging vars
    ERROR:Shouter:ExampleClass.perform_action_chain_2:Saving env



```python
ec.logger.return_last_words(
    # optional
    env_persist_path = 'environment.dill'
)
```




    {'a': 1,
     'b': 'b',
     'c': ['list'],
     'd': {'key': 'value'},
     'e': Shouter(supported_classes=(), dotline_length=50, auto_output_type_selection=True, show_function=True, show_traceback=False, show_idx=False, tears_persist_path='log_records.json', env_persist_path='environment.dill', datetime_format='%Y-%m-%d %H:%M:%S', log_records=[], persist_env=False, lock=<unlocked _thread.lock object at 0x70ed6cd6f940>, last_traceback=[], log_plotter_h=None, log_plotter_class=<class 'shouterlog.shouterlog.LogPlotter'>, log_plotter_params={}, loggerLvl=20, logger_name=None, logger_format='%(levelname)s:%(name)s:%(message)s')}



### 8. Plotting execution flow and reviewing steps


```python
import attrsx

@attrsx.define(handler_specs={
    "example1" : ExampleClass
},
    logger_chaining={
    'logger' : True
})
class MainExampleClass:

    def __attrs_post_init__(self):

        self._initialize_example1_h()

    def print_example_print(self):

        self.logger.debug("Printing from example!", label = "START")

        for i in range(5):

            self.example1_h.print_debug()

        self.logger.debug("Printing from example!", label = "END")

```


```python
shouter_for_main_example_class = Shouter(
    supported_classes = (MainExampleClass, ExampleClass,),
    tears_persist_path = 'log_records2.json',
    loggerLvl=logging.DEBUG
)

mec = MainExampleClass(logger=shouter_for_main_example_class)

mec.print_example_print()
```

    DEBUG:Shouter:MainExampleClass.print_example_print:Printing from example!
    DEBUG:Shouter:ExampleClass.print_debug:+ This is a debug message!
    DEBUG:Shouter:ExampleClass.print_debug:+ This is a debug message!
    DEBUG:Shouter:ExampleClass.print_debug:+ This is a debug message!
    DEBUG:Shouter:ExampleClass.print_debug:+ This is a debug message!
    DEBUG:Shouter:ExampleClass.print_debug:+ This is a debug message!
    DEBUG:Shouter:MainExampleClass.print_example_print:Printing from example!



```python
mec.logger.show_sequence_diagram()
```


    
![png](output_22_0.png)
    



```python
mec.logger.show_logs_by_id(ids = [1,2])
```




    [{'idx': 1,
      'call_id': 124165157051456,
      'datetime': '2026-01-05 23:34:12',
      'level': 'debug',
      'function': 'MainExampleClass.print_example_print',
      'mess': 'Printing from example!',
      'line': 17,
      'lines': [17],
      'is_proc': False,
      'proc_name': 'Task-2',
      'traceback': ['MainExampleClass.print_example_print'],
      'label': 'START',
      'env': {}},
     {'idx': 2,
      'call_id': 109462141702832,
      'datetime': '2026-01-05 23:34:12',
      'level': 'debug',
      'function': 'ExampleClass.print_debug',
      'mess': 'This is a debug message!',
      'line': 12,
      'lines': [12, 21],
      'is_proc': False,
      'proc_name': 'Task-2',
      'traceback': ['ExampleClass.print_debug',
       'MainExampleClass.print_example_print'],
      'label': None,
      'env': {'a': 0}}]


