# Package Auto Assembler

This tool is meant to streamline creation of single module packages.
Its purpose is to automate as many aspects of python package creation as possible,
to shorten a development cycle of reusable components, maintain certain standard of quality
for reusable code. It provides tool to simplify the process of package creatrion
to a point that it can be triggered automatically within ci/cd pipelines,
with minimal preparations and requirements for new modules.



```python
from package_auto_assembler import (VersionHandler, \
    ImportMappingHandler, RequirementsHandler, MetadataHandler, \
        LocalDependaciesHandler, LongDocHandler, SetupDirHandler, \
            ReleaseNotesHandler, PackageAutoAssembler)
```

## Usage examples

The examples contain: 
1. package versioning
2. import mapping
3. extracting and merging requirements
4. preparing metadata
5. merging local dependacies into single module
6. prepare README
7. assembling setup directory
8. making a package
9. creating release notes from commit messages

### 1. Package versioning

#### Initialize VersionHandler


```python
pv = VersionHandler(
    # required
    versions_filepath = '../tests/package_auto_assembler/lsts_package_versions.yml',
    log_filepath = '../tests/package_auto_assembler/version_logs.csv',
    # optional
    default_version = "0.0.1")
```

#### Add new package


```python
pv.add_package(
    package_name = "new_package",
    # optional
    version = "0.0.1"
)
```

#### Update package version


```python
pv.increment_patch(
    package_name = "new_package"
)
## for not tracked package
pv.increment_patch(
    package_name = "another_new_package",
    # optional
    default_version = "0.0.1"
)
```

    There are no known versions of 'another_new_package', 0.0.1 will be used!


#### Display current versions and logs


```python
pv.get_versions(
    # optional
    versions_filepath = '../tests/package_auto_assembler/lsts_package_versions.yml'
)
```




    {'another_new_package': '0.0.1',
     'example_module': '0.0.1',
     'new_package': '0.0.2'}




```python
pv.get_version(
    package_name='new_package'
)
```




    '0.0.2'




```python
pv.get_logs(
    # optional
    log_filepath = '../tests/package_auto_assembler/version_logs.csv'
)
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
      <th>Timestamp</th>
      <th>Package</th>
      <th>Version</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>2024-01-06 00:54:04</td>
      <td>example_module</td>
      <td>0.0.1</td>
    </tr>
    <tr>
      <th>1</th>
      <td>2024-04-27 22:41:21</td>
      <td>new_package</td>
      <td>0.0.1</td>
    </tr>
    <tr>
      <th>2</th>
      <td>2024-04-27 22:41:21</td>
      <td>new_package</td>
      <td>0.0.2</td>
    </tr>
    <tr>
      <th>3</th>
      <td>2024-04-27 22:41:21</td>
      <td>another_new_package</td>
      <td>0.0.1</td>
    </tr>
  </tbody>
</table>
</div>



#### Flush versions and logs


```python
pv.flush_versions()
pv.flush_logs()
```

### 2. Import mapping

#### Initialize ImportMappingHandler


```python
im = ImportMappingHandler(
    # required
    mapping_filepath = "../env_spec/package_mapping.json"
)
```

#### Load package mappings


```python
im.load_package_mappings(
    # optional
    mapping_filepath = "../env_spec/package_mapping.json"
)
```




    {'PIL': 'Pillow',
     'bs4': 'beautifulsoup4',
     'fitz': 'PyMuPDF',
     'attr': 'attrs',
     'dotenv': 'python-dotenv',
     'googleapiclient': 'google-api-python-client',
     'google_auth_oauthlib': 'google-auth-oauthlib',
     'sentence_transformers': 'sentence-transformers',
     'flask': 'Flask',
     'stdlib_list': 'stdlib-list',
     'sklearn': 'scikit-learn',
     'yaml': 'pyyaml',
     'package_auto_assembler': 'package-auto-assembler'}



### 3. Extracting and merging requirements

#### Initialize RequirementsHandler


```python
rh = RequirementsHandler(
    # optional/required later
    module_filepath = "../tests/package_auto_assembler/example_module.py",
    package_mappings = {'PIL': 'Pillow',
                        'bs4': 'beautifulsoup4',
                        'fitz': 'PyMuPDF',
                        'attr': 'attrs',
                        'dotenv': 'python-dotenv',
                        'googleapiclient': 'google-api-python-client',
                        'sentence_transformers': 'sentence-transformers',
                        'flask': 'Flask',
                        'stdlib_list': 'stdlib-list',
                        'sklearn': 'scikit-learn',
                        'yaml': 'pyyaml'},
    requirements_output_path = "../tests/package_auto_assembler/",
    output_requirements_prefix = "requirements_",
    custom_modules_filepath = "../tests/package_auto_assembler/dependancies",
    python_version = '3.8'
)
```

#### List custom modules for a given directory


```python
rh.list_custom_modules(
    # optional
    custom_modules_filepath="../tests/package_auto_assembler/dependancies"
)
```




    ['example_local_dependacy_2', 'example_local_dependacy_1']



#### Check if module is a standard python library


```python
rh.is_standard_library(
    # required
    module_name = 'example_local_dependacy_1',
    # optional
    python_version = '3.8'
)
```




    False




```python
rh.is_standard_library(
    # required
    module_name = 'logging',
    # optional
    python_version = '3.8'
)
```




    True



#### Extract requirements from the module file


```python
rh.extract_requirements(
    # optional
    module_filepath = "../tests/package_auto_assembler/example_module.py",
    custom_modules = ['example_local_dependacy_2', 'example_local_dependacy_1'],
    package_mappings = {'PIL': 'Pillow',
                        'bs4': 'beautifulsoup4',
                        'fitz': 'PyMuPDF',
                        'attr': 'attrs',
                        'dotenv': 'python-dotenv',
                        'googleapiclient': 'google-api-python-client',
                        'sentence_transformers': 'sentence-transformers',
                        'flask': 'Flask',
                        'stdlib_list': 'stdlib-list',
                        'sklearn': 'scikit-learn',
                        'yaml': 'pyyaml'},
    python_version = '3.8'
)
```




    ['### example_module.py', 'attrs>=22.2.0']



#### Save requirements to a file


```python
rh.write_requirements_file(
    # optional/required later
    module_name = 'example_module',
    requirements = ['### example_module.py', 'attrs>=22.2.0'],
    output_path = "../tests/package_auto_assembler/",
    prefix = "requirements_"
)
```

#### Read requirements


```python
rh.read_requirements_file(
    # required
    requirements_filepath = "../tests/package_auto_assembler/requirements_example_module.txt"
)
```




    ['attrs>=22.2.0']



### 4. Preparing metadata

#### Initializing MetadataHandler


```python
mh = MetadataHandler(
    # optional/required later
    module_filepath = "../tests/package_auto_assembler/example_module.py"
)
```

#### Check if metadata is available


```python
mh.is_metadata_available(
    # optional
    module_filepath = "../tests/package_auto_assembler/example_module.py"
)
```




    True



#### Extract metadata from module


```python
mh.get_package_metadata(
    # optional
    module_filepath = "../tests/package_auto_assembler/example_module.py"
)
```




    {'author': 'Kyrylo Mordan',
     'author_email': 'parachute.repo@gmail.com',
     'version': '0.0.1',
     'description': 'A mock handler for simulating a vector database.',
     'keywords': ['python', 'vector database', 'similarity search']}



### 5. Merging local dependacies into single module

#### Initializing LocalDependaciesHandler


```python
ldh = LocalDependaciesHandler(
    # required
    main_module_filepath = "../tests/package_auto_assembler/example_module.py",
    dependencies_dir = "../tests/package_auto_assembler/dependancies/",
    # optional
    save_filepath = "./combined_example_module.py"
)
```

#### Combine main module with dependacies


```python
print(ldh.combine_modules(
    # optional
    main_module_filepath = "../tests/package_auto_assembler/example_module.py",
    dependencies_dir = "../tests/package_auto_assembler/dependancies/",
    add_empty_design_choices = False
)[0:1000])
```

    """
    Mock Vector Db Handler
    
    This class is a mock handler for simulating a vector database, designed primarily for testing and development scenarios.
    It offers functionalities such as text embedding, hierarchical navigable small world (HNSW) search,
    and basic data management within a simulated environment resembling a vector database.
    """
    
    import logging
    import json
    import time
    import attr #>=22.2.0
    import string
    import os
    import csv
    
    __design_choices__ = {}
    
    @attr.s
    class Shouter:
    
        """
        A class for managing and displaying formatted log messages.
    
        This class uses the logging module to create and manage a logger
        for displaying formatted messages. It provides a method to output
        various types of lines and headers, with customizable message and
        line lengths.
        """
    
        # Formatting settings
        dotline_length = attr.ib(default=50)
    
        # Logger settings
        logger = attr.ib(default=None)
        logger_name = attr.ib(default='Shouter')
        loggerLvl = attr.ib(default=lo



```python
ldh.dependencies_names_list
```




    ['example_local_dependacy_2', 'example_local_dependacy_1']



#### Save combined module


```python
ldh.save_combined_modules(
    # optional
    combined_module = ldh.combine_modules(),
    save_filepath = "./combined_example_module.py"
)
```

### 6. Prepare README


```python
import logging
ldh = LongDocHandler(
    # optional/required later
    notebook_path = "../tests/package_auto_assembler/example_module.ipynb",
    markdown_filepath = "../example_module.md",
    timeout = 600,
    kernel_name = 'python3',
    # logger
    loggerLvl = logging.DEBUG
)
```

#### Convert notebook to md without executing


```python
ldh.convert_notebook_to_md(
    # optional
    notebook_path = "../tests/package_auto_assembler/example_module.ipynb",
    output_path = "../example_module.md"
)
```

    Converted ../tests/package_auto_assembler/example_module.ipynb to ../example_module.md


#### Convert notebook to md with executing


```python
ldh.convert_and_execute_notebook_to_md(
    # optional
    notebook_path = "../tests/package_auto_assembler/example_module.ipynb",
    output_path = "../example_module.md",
    timeout = 600,
    kernel_name = 'python3'
)
```

    Converted and executed ../tests/package_auto_assembler/example_module.ipynb to ../example_module.md


#### Return long description


```python
long_description = ldh.return_long_description(
    # optional
    markdown_filepath = "../example_module.md"
)
```

### 7. Assembling setup directory

#### Initializing SetupDirHandler


```python
sdh = SetupDirHandler(
    # required
    module_filepath = "../tests/package_auto_assembler/example_module.py",
    # optional/ required
    module_name = "example_module",
    metadata = {'author': 'Kyrylo Mordan',
                'version': '0.0.1',
                'description': 'Example module.',
                'long_description' : long_description,
                'keywords': ['python']},
    requirements = ['attrs>=22.2.0'],
    classifiers = ['Development Status :: 3 - Alpha',
                   'Intended Audience :: Developers',
                   'Intended Audience :: Science/Research',
                   'Programming Language :: Python :: 3',
                   'Programming Language :: Python :: 3.9',
                   'Programming Language :: Python :: 3.10',
                   'Programming Language :: Python :: 3.11',
                   'License :: OSI Approved :: MIT License',
                   'Topic :: Scientific/Engineering'],
    setup_directory = "./example_setup_dir"
)
```

#### Create empty setup dir


```python
sdh.flush_n_make_setup_dir(
    # optional
    setup_directory = "./example_setup_dir"
)
```

#### Copy module to setup dir


```python
sdh.copy_module_to_setup_dir(
    # optional
    module_filepath = "./combined_example_module.py",
    setup_directory = "./example_setup_dir"
)
```

#### Create init file


```python
sdh.create_init_file(
    # optional
    module_name = "example_module",
    setup_directory = "./example_setup_dir"
)
```

#### Create setup file


```python
sdh.write_setup_file(
    # optional
    module_name = "example_module",
    metadata = {'author': 'Kyrylo Mordan',
                'version': '0.0.1',
                'description': 'Example Module',
                'keywords': ['python']},
    requirements = ['attrs>=22.2.0'],
    classifiers = ['Development Status :: 3 - Alpha',
                   'Intended Audience :: Developers',
                   'Intended Audience :: Science/Research',
                   'Programming Language :: Python :: 3',
                   'Programming Language :: Python :: 3.9',
                   'Programming Language :: Python :: 3.10',
                   'Programming Language :: Python :: 3.11',
                   'License :: OSI Approved :: MIT License',
                   'Topic :: Scientific/Engineering'],
    setup_directory = "./example_setup_dir"
)
```

### 8. Making a package

#### Initializing PackageAutoAssembler


```python
paa = PackageAutoAssembler(
    # required
    module_name = "example_module",
    module_filepath  = "../tests/package_auto_assembler/example_module.py",
    # optional
    mapping_filepath = "../env_spec/package_mapping.json",
    dependencies_dir = "../tests/package_auto_assembler/dependancies/",
    example_notebook_path = "./mock_vector_database.ipynb",
    versions_filepath = '../tests/package_auto_assembler/lsts_package_versions.yml',
    log_filepath = '../tests/package_auto_assembler/version_logs.csv',
    setup_directory = "./example_module",
    classifiers = ['Development Status :: 3 - Alpha',
                    'Intended Audience :: Developers',
                    'Intended Audience :: Science/Research',
                    'Programming Language :: Python :: 3',
                    'Programming Language :: Python :: 3.9',
                    'Programming Language :: Python :: 3.10',
                    'Programming Language :: Python :: 3.11',
                    'License :: OSI Approved :: MIT License',
                    'Topic :: Scientific/Engineering'],
    requirements_list = [],
    execute_readme_notebook = True,
    python_version = "3.8",
    version_increment_type = "patch",
    default_version = "0.0.1"
)
```

#### Add metadata from module


```python
paa.add_metadata_from_module(
    # optional
    module_filepath  = "../tests/package_auto_assembler/example_module.py"
)
```

#### Add or update version


```python
paa.add_or_update_version(
    # optional
    module_name = "example_module",
    version_increment_type = "patch",
    version = "0.0.1",
    versions_filepath = '../tests/package_auto_assembler/lsts_package_versions.yml',
    log_filepath = '../tests/package_auto_assembler/version_logs.csv'
)
```

    There are no known versions of 'example_module', 0.0.1 will be used!


#### Prepare setup directory


```python
paa.prep_setup_dir()
```

#### Merge local dependacies


```python
paa.merge_local_dependacies(
    # optional
    main_module_filepath = "../tests/package_auto_assembler/example_module.py",
    dependencies_dir= "../tests/package_auto_assembler/dependancies/",
    save_filepath = "./example_module/example_module.py"
)
```

#### Add requirements from module


```python
paa.add_requirements_from_module(
    # optional
    module_filepath = "../tests/package_auto_assembler/example_module.py",
    import_mappings = {'PIL': 'Pillow',
                        'bs4': 'beautifulsoup4',
                        'fitz': 'PyMuPDF',
                        'attr': 'attrs',
                        'dotenv': 'python-dotenv',
                        'googleapiclient': 'google-api-python-client',
                        'sentence_transformers': 'sentence-transformers',
                        'flask': 'Flask',
                        'stdlib_list': 'stdlib-list',
                        'sklearn': 'scikit-learn',
                        'yaml': 'pyyaml'}
)
```

#### Make README out of example notebook


```python
paa.add_readme(
    # optional
    example_notebook_path = "../tests/package_auto_assembler/example_module.ipynb",
    output_path = "./example_module/README.md",
    execute_notebook=False,
)
```


```python
paa.requirements_list
```




    ['### example_module.py', 'attrs>=22.2.0']



#### Prepare setup file


```python
paa.prep_setup_file(
    # optional
    metadata = {'author': 'Kyrylo Mordan',
                'version': '0.0.1',
                'description': 'Example module',
                'keywords': ['python']},
    requirements = ['### example_module.py',
                    'attr>=22.2.0'],
    classifiers = ['Development Status :: 3 - Alpha',
                    'Intended Audience :: Developers',
                    'Intended Audience :: Science/Research',
                    'Programming Language :: Python :: 3',
                    'Programming Language :: Python :: 3.9',
                    'Programming Language :: Python :: 3.10',
                    'Programming Language :: Python :: 3.11',
                    'License :: OSI Approved :: MIT License',
                    'Topic :: Scientific/Engineering']

)
```

#### Make package


```python
paa.make_package(
    # optional
    setup_directory = "./example_module"
)
```




    CompletedProcess(args=['python', './example_module/setup.py', 'sdist', 'bdist_wheel'], returncode=1, stdout='', stderr="usage: setup.py [global_opts] cmd1 [cmd1_opts] [cmd2 [cmd2_opts] ...]\n   or: setup.py --help [cmd1 cmd2 ...]\n   or: setup.py --help-commands\n   or: setup.py cmd --help\n\nerror: invalid command 'bdist_wheel'\n")



### 9. Creating release notes from commit messages


```python
rnh = ReleaseNotesHandler(
    # path to existing or new release notes file
    filepath = '../tests/package_auto_assembler/release_notes.md',
    # name of label in commit message [example_module] for filter
    label_name = 'example_module',
    # new version to be used in release notes
    version = '0.0.2'
)
```

    No relevant commit messages found!


    ..trying depth 2 !


    No relevant commit messages found!


    No messages to clean were provided


##### - overwritting commit messages fro example


```python
# commit messages from last merge
rnh.commit_messages
```




    ['Update requirements']




```python
example_commit_messages = [
    '[example_module] usage example for initial release notes; bugfixes for RNH',
    '[BUGFIX] missing parameterframe usage example and reduntant png file',
    '[example_module] initial release notes handler',
    'Update README',
    'Update requirements'
]
rnh.commit_messages = example_commit_messages
```

##### - internal methods that run on intialiazation of ReleaseNotesHandler


```python
# get messages relevant only for label
rnh._filter_commit_messages_by_package()
print("Example filtered_messaged:")
print(rnh.filtered_messages)
# clean messages
rnh._clean_and_split_commit_messages()
print("Example processed_messages:")
print(rnh.processed_messages)
# augment existing release note with new entries or create new
rnh._create_release_note_entry()
print("Example processed_note_entries:")
print(rnh.processed_note_entries)
```

    Example filtered_messaged:
    ['[example_module] usage example for initial release notes; bugfixes for RNH', '[example_module] initial release notes handler']
    Example processed_messages:
    ['usage example for initial release notes', 'bugfixes for RNH', 'initial release notes handler']
    Example processed_note_entries:
    ['# Release notes\n', '\n', '### 0.0.2\n\n    - usage example for initial release notes\n    - bugfixes for RNH\n    - initial release notes handler\n\n', '### 0.0.1\n', '\n', '    - initial version of example_module\n']


##### - saving updated relese notes


```python
rnh.existing_contents
```




    ['# Release notes\n',
     '\n',
     '### 0.0.1\n',
     '\n',
     '    - initial version of example_module\n']




```python
rnh.save_release_notes()
```


```python
# updated content
rnh.get_release_notes_content()
```




    ['# Release notes\n',
     '\n',
     '### 0.0.2\n',
     '\n',
     '    - usage example for initial release notes\n',
     '    - bugfixes for RNH\n',
     '    - initial release notes handler\n',
     '\n',
     '### 0.0.1\n',
     '\n',
     '    - initial version of example_module\n']


