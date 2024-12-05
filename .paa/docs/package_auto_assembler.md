The following includes additional details to how some features of the packages work with examples that involve internal components. Even though using the package this way is very much possible, [cli interface](https://kiril-mordan.github.io/reusables/package_auto_assembler/cli_tools) is recomended. 


```python
from package_auto_assembler import (VersionHandler, \
    ImportMappingHandler, RequirementsHandler, MetadataHandler, \
        LocalDependaciesHandler, LongDocHandler, SetupDirHandler, \
            ReleaseNotesHandler, MkDocsHandler, PackageAutoAssembler, \
                DependenciesAnalyser)
```

### 1. Package versioning

Package versioning within paa is done based on semantic versioning.

`major.minor.patch`

By default, patch is updated, but the minor and major could also be update based on, for example, commit messages or manually from the log file. 

Package auto assembler does try to pull latest version from package storage, but in case of failure uses version logs stored in `.paa/tracking`.

---

initialize VersionHandler


```python
pv = VersionHandler(
    # required
    versions_filepath = '../tests/package_auto_assembler/other/lsts_package_versions.yml',
    log_filepath = '../tests/package_auto_assembler/other/version_logs.csv',
    # optional
    default_version = "0.0.1")
```

add new package


```python
pv.add_package(
    package_name = "new_package",
    # optional
    version = "0.0.1"
)
```

update package version


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


display current versions and logs


```python
pv.get_versions(
    # optional
    versions_filepath = '../tests/package_auto_assembler/other/lsts_package_versions.yml'
)
```




    {'another_new_package': '0.0.1', 'new_package': '0.0.2'}




```python
pv.get_version(
    package_name='new_package'
)
```




    '0.0.2'




```python
pv.get_logs(
    # optional
    log_filepath = '../tests/package_auto_assembler/other/version_logs.csv'
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
      <td>2024-07-29 03:26:39</td>
      <td>new_package</td>
      <td>0.0.1</td>
    </tr>
    <tr>
      <th>1</th>
      <td>2024-07-29 03:26:40</td>
      <td>new_package</td>
      <td>0.0.2</td>
    </tr>
    <tr>
      <th>2</th>
      <td>2024-07-29 03:26:40</td>
      <td>another_new_package</td>
      <td>0.0.1</td>
    </tr>
  </tbody>
</table>
</div>



flush versions and logs


```python
pv.flush_versions()
pv.flush_logs()
```

get latest available version with pip


```python
pv.get_latest_pip_version(package_name = 'package-auto-assembler')
```




    '0.3.1'



### 2. Import mapping

Install and import names of dependencies may vary. The mapping files maps import names to install names so that requirements extraction from `.py` files is possible. Some of the mapping are packaged and would not need to provided, but in case a dependency used within new package was not inluded, it is possible to augment default mapping through `.paa/package_mapping.json`.

---

initialize ImportMappingHandler


```python
im = ImportMappingHandler(
    # required
    mapping_filepath = "../env_spec/package_mapping.json"
)
```

load package mappings


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
     'package_auto_assembler': 'package-auto-assembler',
     'git': 'gitpython'}



### 3. Extracting and merging requirements

Maintaining requirements is much simpler, when done automatically based on the `.py` files. 

The actual requirements files is still constructed. Standard libraries are not added, others are added with their versions, if specified. Local files are also used as dependencies, from which imports are extracted as well. 

For example:

```python
import os
import pandas
import attr #>=22.2.0
from .components.local_dep import *
```

produces 

``` txt
pandas
attrs >=22.2.0
yaml
```

as requirements file, where `yaml` is extracted from `local_dep.py` file.

Checking dependecies for vulnerabilities is usefull and it is done with `pip audit` which is integrated into the paa package and is used by default.

Optional requirements for `extras_require` could be probided the same way normal requirements are, but each like that contains an import like that should be commented out in a special way, starting with `#!`, for example:

```python
import os
import pandas
import attr #>=22.2.0
#! import hnswlib #==0.8.0
```

produces

``` txt
pandas
attrs >=22.2.0
hnswlib==0.8.0; extra == "hnswlib"
```

Sometimes automatic translation of import names to install names via `package_mapping.json`, for packages where these names differ, may not be enough. A manual overwrite can be done with exlusion of some dependencies from automatic extraction pipeline with `#-` comment next to import and `#@` prefix before text that is intended to end up in an equivalent requirements file, for example:

```python
import os
import pandas
import attr #>=22.2.0
import tensorflow #-
#@ tensorflow-gpu
```

produces


``` txt
pandas
attrs >=22.2.0
tensorflow-gpu
```

---

initialize RequirementsHandler


```python
rh = RequirementsHandler(
    # optional/required later
    module_filepath = "../tests/package_auto_assembler/other/example_module.py",
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
    requirements_output_path = "../tests/package_auto_assembler/other/",
    output_requirements_prefix = "requirements_",
    custom_modules_filepath = "../tests/package_auto_assembler/dependancies",
    python_version = '3.8',
    add_header = True
)
```

list custom modules for a given directory


```python
rh.list_custom_modules(
    # optional
    custom_modules_filepath="../tests/package_auto_assembler/dependancies"
)
```




    ['example_local_dependacy_1', 'example_local_dependacy_2']



check if module is a standard python library


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



extract requirements from the module file


```python
rh.extract_requirements(
    # optional
    module_filepath = "../tests/package_auto_assembler/other/example_module.py",
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
    python_version = '3.8',
    add_header=True
)
```




    (['attrs>=22.2.0'],
     ['torch<=2.4.1', 'fastapi[all]', 'scikit-learn==1.5.1', 'numpy'])




```python
rh.requirements_list
```




    ['attrs>=22.2.0']




```python
rh.optional_requirements_list
```




    ['torch<=2.4.1', 'fastapi[all]', 'scikit-learn==1.5.1', 'numpy']



audit dependencies


```python
rh.check_vulnerabilities(
    # optional if ran extract_requirements() before
    requirements_list = None,
    raise_error = True
)
```

    No known vulnerabilities found
    


    



```python
rh.vulnerabilities
```




    []




```python
try:
    rh.check_vulnerabilities(
        # optional if ran extract_requirements() before
        requirements_list = ['attrs>=22.2.0', 'pandas', 'hnswlib==0.7.0'],
        raise_error = True
    )
except Exception as e:
    print(f"Error: {e}")
```

    Found 1 known vulnerability in 1 package
    


    Name    Version ID                  Fix Versions
    ------- ------- ------------------- ------------
    hnswlib 0.7.0   GHSA-xwc8-rf6m-xr86
    
    Error: Found vulnerabilities, resolve them or ignore check to move forwards!



```python
rh.vulnerabilities
```




    [{'name': 'hnswlib',
      'version': '0.7.0',
      'id': 'GHSA-xwc8-rf6m-xr86',
      'fix_versions': None}]



save requirements to a file


```python
rh.write_requirements_file(
    # optional/required later
    module_name = 'example_module',
    requirements = ['### example_module.py', 'attrs>=22.2.0'],
    output_path = "../tests/package_auto_assembler/other/",
    prefix = "requirements_"
)
```

read requirements


```python
rh.read_requirements_file(
    # required
    requirements_filepath = "../tests/package_auto_assembler/other/requirements_example_module.txt"
)
```




    ['attrs>=22.2.0']



### 4. Preparing metadata

Since all of the necessary information for building a package needs to be contained within main component `.py` file, basic metadata is provided with the use of `__package_metadata__` dictionary object, defined within that `.py` file. It is also used as a trigger for package building within paa pipeline. 

Even though some general information shared between packages could be provided through general config, but package specific info should be provided through `__package_metadata__`. It should support most text fields from setup file, but for others the following fields are available:

- `classifiers`: adds classifiers to the general ones from config, unless it's `Development Status :: ` then module level definition will overwrite the one from config
- `extras_require`: a dictionary of optional package that wouldn't be installed during normal installation. The key could be used during installation and the value would be a list of dependencies.
- `install_requires` : adds requirements to the list read from imports

\* Note that providing dependencies this way does not check them through pip-audit or translate them through package mapping

---


initializing MetadataHandler


```python
mh = MetadataHandler(
    # optional/required later
    module_filepath = "../tests/package_auto_assembler/other/example_module.py"
)
```

check if metadata is available


```python
mh.is_metadata_available(
    # optional
    module_filepath = "../tests/package_auto_assembler/other/example_module.py"
)
```




    True



extract metadata from module


```python
mh.get_package_metadata(
    # optional
    module_filepath = "../tests/package_auto_assembler/other/example_module.py"
)
```




    {'author': 'Kyrylo Mordan',
     'author_email': 'parachute.repo@gmail.com',
     'version': '0.0.1',
     'description': 'A mock handler for simulating a vector database.',
     'keywords': ['python', 'vector database', 'similarity search']}



### 5. Merging local dependacies into single module

Package auto assembler creates `single module packages`, meaning that once package is built all of the object are imported from a single place. The packaging tool does allow for `local dependecies` which are `.py` files imported from specified dependencies directory and its subfolders. Packaging structure may look like the following:

```
packaging repo/
└src/
  ├ <package names>.py
  └ components
    ├local_dependecy.py
    └subdir_1
      └local_dependency_2.py 
```

During packaging process paa merges main module with its local dependies into a single file.

---

initializing LocalDependaciesHandler


```python
ldh = LocalDependaciesHandler(
    # required
    main_module_filepath = "../tests/package_auto_assembler/other/example_module.py",
    dependencies_dir = "../tests/package_auto_assembler/dependancies/",
    # optional
    save_filepath = "./combined_example_module.py"
)
```

combine main module with dependacies


```python
print(ldh.combine_modules(
    # optional
    main_module_filepath = "../tests/package_auto_assembler/other/example_module.py",
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
    import sklearn
    
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
        loggerLvl = attr.ib(default=logging.DEBUG)
        log



```python
ldh.dependencies_names_list
```




    ['example_local_dependacy_2', 'example_local_dependacy_1', 'dep_from_bundle_1']



save combined module


```python
ldh.save_combined_modules(
    # optional
    combined_module = ldh.combine_modules(),
    save_filepath = "./combined_example_module.py"
)
```

### 6. Prepare README

Package description is based on `.ipynb` with same name as the `.py`. By default it is converted to markdown as is, but there is also an option to execute it.

---


```python
import logging
ldh = LongDocHandler(
    # optional/required later
    notebook_path = "../tests/package_auto_assembler/other/example_module.ipynb",
    markdown_filepath = "../example_module.md",
    timeout = 600,
    kernel_name = 'python3',
    # logger
    loggerLvl = logging.DEBUG
)
```

convert notebook to md without executing


```python
ldh.convert_notebook_to_md(
    # optional
    notebook_path = "../tests/package_auto_assembler/other/example_module.ipynb",
    output_path = "../example_module.md"
)
```

    Converted ../tests/package_auto_assembler/example_module.ipynb to ../example_module.md


convert notebook to md with executing


```python
ldh.convert_and_execute_notebook_to_md(
    # optional
    notebook_path = "../tests/package_auto_assembler/other/example_module.ipynb",
    output_path = "../example_module.md",
    timeout = 600,
    kernel_name = 'python3'
)
```

    Converted and executed ../tests/package_auto_assembler/example_module.ipynb to ../example_module.md


return long description


```python
long_description = ldh.return_long_description(
    # optional
    markdown_filepath = "../example_module.md"
)
```

### 7. Assembling setup directory

Packages are created following rather simple sequence of steps. At some point of the process a temporary directory is created to store the following files:

- `__init__.py` is a simple import from a single module
- `<package name>.py` is a single module with all of the local dependecies
- `cli.py` is optional packaged cli tool
- `routes.py` is optional packaged file with fastapi routes
- `streamlit.py` is optional packaged streamlit app
- `setup.py` is a setup file for making a package
- `README.md` is a package description file based on `.ipynb` file
- `LICENSE` is optional license file
- `MANIFEST.in` is a list of additional files to be included with the package
- `mkdocs` is a folder with built mkdocs site based on optional `extra_docs` for the module, module docstring and `README.md`
- `artifacts` contains optional files that would be packaged with the module
- `tests` contains files needed to run tests with [`pytest`](https://docs.pytest.org/en/stable/)
- `.paa.tracking` contains tracking files from `.paa` dir to make each release of the package independent of PPR that released it

---


initializing SetupDirHandler


```python
sdh = SetupDirHandler(
    # required
    module_filepath = "../tests/package_auto_assembler/other/example_module.py",
    # optional/ required
    module_name = "example_module",
    metadata = {'author': 'Kyrylo Mordan',
                'version': '0.0.1',
                'description': 'Example module.',
                'long_description' : long_description,
                'keywords': ['python']},
    license_path = "../LICENSE",
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

create empty setup dir


```python
sdh.flush_n_make_setup_dir(
    # optional
    setup_directory = "./example_setup_dir"
)
```

copy module to setup dir


```python
sdh.copy_module_to_setup_dir(
    # optional
    module_filepath = "./combined_example_module.py",
    setup_directory = "./example_setup_dir"
)
```

copy license to setup dir


```python
sdh.copy_module_to_setup_dir(
    # optional
    license_path = "../LICENSE",
    setup_directory = "./example_setup_dir"
)
```

create init file


```python
sdh.create_init_file(
    # optional
    module_name = "example_module",
    setup_directory = "./example_setup_dir"
)
```

create setup file


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

### 8. Creating release notes from commit messages

Package versioning could be enhanced with release notes. Since the tool is mainly meant for ci/cd, it takes advantage of commit messages to construct a release note for every version. 

Commit history is analysed from the last merge, if nothiong found then the next and the next, until at least one of `[<package name>]` labels are found within commit messages. They are bundled together to for a note, where each commit message or messages deliminated with `;` are turned in a list element. Previos notes are used to establish which part of commit history to use as a starting point.

Commit messages could also be used to increment version by something other then a default patch. 

- `[<package name>][..+]` increments patch (default behavior)
- `[<package name>][.+.]` increments minor
- `[<package name>][+..]` increments major
- `[<package name>][0.1.2]` forces specific version `0.1.2`

\* First release within new packaging repo may struggle to extract release note since commit messages are only analysed from merges in the commit history. 

---



```python
rnh = ReleaseNotesHandler(
    # path to existing or new release notes file
    filepath = '../tests/package_auto_assembler/other/release_notes.md',
    # name of label in commit message [example_module] for filter
    label_name = 'example_module',
    # new version to be used in release notes
    version = '0.0.1'
)
```

    No relevant commit messages found!
    ..trying depth 2 !
    No relevant commit messages found!
    No messages to clean were provided


overwritting commit messages from example


```python
# commit messages from last merge
rnh.commit_messages
```




    ['fixing paa tests',
     'fixing paa tests',
     'fixing paa tests',
     '[package_auto_assembler] increasing default max search depth for commit history to 5',
     'fixing mocker-db release notes',
     'Update package version tracking files',
     'Update README',
     'Update requirements']




```python
example_commit_messages = [
    '[example_module] usage example for initial release notes; bugfixes for RNH',
    '[BUGFIX] missing parameterframe usage example and reduntant png file',
    '[example_module][0.1.2] initial release notes handler',
    'Update README',
    'Update requirements'
]
rnh.commit_messages = example_commit_messages
```

internal methods that run on intialiazation of ReleaseNotesHandler


```python
# get messages relevant only for label
rnh._filter_commit_messages_by_package()
print("Example filtered_messaged:")
print(rnh.filtered_messages)

# clean messages
rnh._clean_and_split_commit_messages()
print("Example processed_messages:")
print(rnh.processed_messages)
```

    Example filtered_messaged:
    ['[example_module] usage example for initial release notes; bugfixes for RNH', '[example_module][0.1.2] initial release notes handler']
    Example processed_messages:
    ['usage example for initial release notes', 'bugfixes for RNH', 'initial release notes handler']


get version update from relevant messages


```python
version_update = rnh.extract_latest_version()
print(f"Example version_update: {version_update}")
```

    Example version_update: 0.1.2


get latest version from relevant release notes


```python
latest_version = rnh.extract_latest_version()
print(f"Example latest_version: {latest_version}")
```

    Example latest_version: 0.1.2


augment existing release note with new entries or create new


```python
# augment existing release note with new entries or create new
rnh.create_release_note_entry(
    # optional
    existing_contents=rnh.existing_contents,
    version=rnh.version,
    new_messages=rnh.processed_messages
)
print("Example processed_note_entries:")
print(rnh.processed_note_entries)
```

    Example processed_note_entries:
    ['# Release notes\n', '\n', '### 0.1.2\n', '\n', '    - usage example for initial release notes\n', '\n', '    - bugfixes for RNH\n', '\n', '    - initial release notes handler\n', '\n', '### 0.0.1\n', '\n', '    - initial version of example_module\n']


saving updated relese notes


```python
rnh.existing_contents
```




    ['# Release notes\n',
     '\n',
     '### 0.1.2\n',
     '\n',
     '    - usage example for initial release notes\n',
     '    - bugfixes for RNH\n',
     '    - initial release notes handler\n',
     '### 0.1.2\n',
     '\n',
     '    - usage example for initial release notes\n',
     '\n',
     '    - bugfixes for RNH\n',
     '\n',
     '    - initial release notes handler\n',
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
     '### 0.1.2\n',
     '\n',
     '    - usage example for initial release notes\n',
     '\n',
     '    - bugfixes for RNH\n',
     '\n',
     '    - initial release notes handler\n',
     '\n',
     '### 0.0.1\n',
     '\n',
     '    - initial version of example_module\n']



### 9. Analysing package dependencies

Extracting info from installed dependencies can provide important insight into inner workings of a package and help avoid some of the licenses. 

Licenses are extracted from package metadata and normalized for analysis. Missing labels are marked with `-` and not recognized licenses with `unknown`.

Information about unrecognized license labels could be provided through `.paa/package_licenses json` file that would contain install package name and corresponding license label.

---


```python
da = DependenciesAnalyser(
    # optional
    package_name = 'mocker-db',
    package_licenses_filepath = '../tests/package_auto_assembler/other/package_licenses.json',
    allowed_licenses = ['mit', 'apache-2.0', 'lgpl-3.0', 'bsd-3-clause', 'bsd-2-clause', '-', 'mpl-2.0']
)
```

finding installed packages with a list of tags


```python
da.filter_packages_by_tags(tags=['aa-paa-tool'])
```




    [('comparisonframe', '0.0.0'),
     ('mocker-db', '0.0.1'),
     ('package-auto-assembler', '0.0.0'),
     ('proompter', '0.0.0')]



extracting some metadata from the installed package


```python
package_metadata = da.get_package_metadata(
    package_name = 'mocker-db'
)
package_metadata
```




    {'keywords': ['aa-paa-tool'],
     'version': '0.0.1',
     'author': 'Kyrylo Mordan',
     'author_email': 'parachute.repo@gmail.com',
     'classifiers': ['Development Status :: 3 - Alpha',
      'Intended Audience :: Developers',
      'Intended Audience :: Science/Research',
      'Programming Language :: Python :: 3',
      'Programming Language :: Python :: 3.9',
      'Programming Language :: Python :: 3.10',
      'Programming Language :: Python :: 3.11',
      'License :: OSI Approved :: MIT License',
      'Topic :: Scientific/Engineering',
      'PAA-Version :: 0.4.3',
      'PAA-CLI :: False'],
     'paa_version': '0.4.3',
     'paa_cli': 'False',
     'license_label': 'MIT'}



extracting package requirements


```python
package_requirements = da.get_package_requirements(
    package_name = 'mocker-db'
)
package_requirements
```




    ['requests',
     'attrs >=22.2.0',
     'httpx',
     'hnswlib ==0.8.0',
     'gridlooper ==0.0.1',
     'dill ==0.3.7',
     'numpy ==1.26.0',
     "sentence-transformers ; extra == 'sentence_transformers'"]



extracting tree of dependencies


```python
extracted_dependencies_tree = da.extract_dependencies_tree(
    package_name = 'mocker-db'
)
extracted_dependencies_tree
```




    {'requests': {'charset-normalizer': [],
      'idna': [],
      'urllib3': [],
      'certifi': []},
     'attrs': {'importlib-metadata': {'zipp': [], 'typing-extensions': []}},
     'httpx': {'anyio': {'idna': [],
       'sniffio': [],
       'exceptiongroup': [],
       'typing-extensions': []},
      'certifi': [],
      'httpcore': {'certifi': [], 'h11': {'typing-extensions': []}},
      'idna': [],
      'sniffio': []},
     'hnswlib': {'numpy': []},
     'gridlooper': {'dill': [],
      'attrs': {'importlib-metadata': {'zipp': [], 'typing-extensions': []}},
      'tqdm': {'colorama': []}},
     'dill': [],
     'numpy': []}



addding license labels to tree of dependencies


```python
extracted_dependencies_tree_license = da.add_license_labels_to_dep_tree(
    dependencies_tree = extracted_dependencies_tree
)
extracted_dependencies_tree_license
```




    {'requests': 'apache-2.0',
     'requests.charset-normalizer': '-',
     'requests.idna': '-',
     'requests.urllib3': '-',
     'requests.certifi': 'mpl-2.0',
     'attrs': '-',
     'attrs.importlib-metadata': '-',
     'attrs.importlib-metadata.zipp': '-',
     'attrs.importlib-metadata.typing-extensions': '-',
     'httpx': '-',
     'httpx.anyio': 'mit',
     'httpx.anyio.idna': '-',
     'httpx.anyio.sniffio': '-',
     'httpx.anyio.exceptiongroup': '-',
     'httpx.anyio.typing-extensions': '-',
     'httpx.certifi': 'mpl-2.0',
     'httpx.httpcore': '-',
     'httpx.httpcore.certifi': 'mpl-2.0',
     'httpx.httpcore.h11': 'mit',
     'httpx.httpcore.h11.typing-extensions': '-',
     'httpx.idna': '-',
     'httpx.sniffio': '-',
     'hnswlib': '-',
     'hnswlib.numpy': 'bsd-3-clause',
     'gridlooper': '-',
     'gridlooper.dill': 'bsd-3-clause',
     'gridlooper.attrs': '-',
     'gridlooper.attrs.importlib-metadata': '-',
     'gridlooper.attrs.importlib-metadata.zipp': '-',
     'gridlooper.attrs.importlib-metadata.typing-extensions': '-',
     'gridlooper.tqdm': '-',
     'gridlooper.tqdm.colorama': '-',
     'dill': 'bsd-3-clause',
     'numpy': 'bsd-3-clause'}



printing extracted tree of dependencies


```python
da.print_flattened_tree(extracted_dependencies_tree_license)
```

    └── requests : apache-2.0
        ├── charset-normalizer : -
        ├── idna : -
        ├── urllib3 : -
        └── certifi : mpl-2.0
    └── attrs : -
        └── importlib-metadata : -
            ├── zipp : -
            └── typing-extensions : -
    └── httpx : -
        ├── anyio : mit
            ├── idna : -
            ├── sniffio : -
            ├── exceptiongroup : -
            └── typing-extensions : -
        ├── certifi : mpl-2.0
        ├── httpcore : -
            ├── certifi : mpl-2.0
            └── h11 : mit
                └── typing-extensions : -
        ├── idna : -
        └── sniffio : -
    └── hnswlib : -
        └── numpy : bsd-3-clause
    └── gridlooper : -
        ├── dill : bsd-3-clause
        ├── attrs : -
            └── importlib-metadata : -
                ├── zipp : -
                └── typing-extensions : -
        └── tqdm : -
            └── colorama : -
    └── dill : bsd-3-clause
    └── numpy : bsd-3-clause


filtering for unexpected licenses in tree of dependencies


```python
allowed_licenses = ['mit', 'apache-2.0', 'lgpl-3.0', 'mpl-2.0', '-']

da.find_unexpected_licenses_in_deps_tree(
    tree_dep_license = extracted_dependencies_tree_license,
    # optional
    allowed_licenses = allowed_licenses,
    raise_error = True
)
```

    {'hnswlib': '', 'gridlooper': ''}
    └── dill : bsd-3-clause
    └── numpy : bsd-3-clause
    └── hnswlib : 
        └── numpy : bsd-3-clause
    └── gridlooper : 
        └── dill : bsd-3-clause



    ---------------------------------------------------------------------------

    Exception                                 Traceback (most recent call last)

    Cell In[9], line 3
          1 allowed_licenses = ['mit', 'apache-2.0', 'lgpl-3.0', 'mpl-2.0', '-']
    ----> 3 da.find_unexpected_licenses_in_deps_tree(
          4     tree_dep_license = extracted_dependencies_tree_license,
          5     # optional
          6     allowed_licenses = allowed_licenses,
          7     raise_error = True
          8 )


    File ~/miniforge3/envs/testenv/lib/python3.10/site-packages/package_auto_assembler/package_auto_assembler.py:2670, in DependenciesAnalyser.find_unexpected_licenses_in_deps_tree(self, tree_dep_license, allowed_licenses, raise_error)
       2668 if raise_error and out != {}:
       2669     self.print_flattened_tree(flattened_dict = out)
    -> 2670     raise Exception("Found unexpected licenses!")
       2671 else:
       2672     self.logger.info("No unexpected licenses found")


    Exception: Found unexpected licenses!


### 10. Adding cli interfaces

The tool allows to make a package with optional cli interfaces. These could be sometimes preferable when a package contains a standalone tool that would be called from script anyway.

All of the cli logic would need to be included within a `.py` file which should be stored within `cli_dir` provided in `.paa.config`. 
Dependencies from these files are extracted in the similar manner to the main module.

Tools from main `.py` file could still be imported like the following:

```python
from package_name.package_name import ToBeImported
```

The code is wired in `setup.py` via the following automatically assuming that appropriate file with the same name as the package exists within `cli_dir` location.

```python
...,
entry_points = {'console_scripts': [
    '<package_alias> = package_name.cli:cli']} ,
...
```

Alias for name could be provided via the following piece of code, defined after imports, otherwise package name would be used.

```python 
__cli_metadata__ = {
    "name" : <package_alias>
}
```

Package-auto-assembler tool itself uses [`click`](https://pypi.org/project/click/) dependency to build that file, use its [cli definition](https://github.com/Kiril-Mordan/reusables/blob/main/cli/package_auto_assembler.py) as example.



### 11. Adding routes and running FastAPI application

The tool allows to make a package with optional routes for FastAPI application and run them. Each packages can have one routes file where its logic should be defined. Package-auto-assembler itself can combine multiple routes from packages and filepaths into one application.

A `.py`  file with the same name of the package should be stored within `api_routes_dir` provided in `.paa.config`.

Dependencies from these files are extracted in the similar manner to the main module.

Tools from main `.py` file could still be imported like the following:

```python
from package_name.package_name import ToBeImported
```

Api description, middleware and run parameters could be provided via optional `.paa.api.config` file, which for example would look like:

```
DESCRIPTION : {
    'version' : 0.0.0
}
MIDDLEWARE : {
    allow_origins : ['*']
}
RUN : {
 host : 0.0.0.0
}
```

where DESCRIPTION contains parameters for `FastAPI`, MIDDLEWARE for `CORSMiddleware` and RUN for `uvicorn.run`


### 12. Adding ui and running streamlit application

The tools allows to make a package with optional [`streamlit`](https://streamlit.io/) application as interface to the packaged code.  Each package can have one streamlit file. Package-auto-assembler itself would then be used to run packaged applications from the package. 

A `.py`  file with the same name of the package should be stored within `streamlit_dir` provided in `.paa.config`.

Dependencies from these files are extracted in the similar manner to the main module.

Tools from main `.py` file could still be imported like the following:

```python
from package_name import ToBeImported
```

Config file with server, theme and other settings can be provided via optional `.paa.streamlit.config`. 


### 13 Adding artifacts to packages

The tool allows to add files to packages that could be accessed from the package or extracted into selected directory.

There are different types of artifacts with a package like this:

- `.paa.tracking` : includes some tracking files for the purposes of the tool, added to every package
- `mkdocs` : optional static mkdocs site 
- `artifacts` contains directories, files and links to files copied from `artifacts_dir/<package_name>` (from `.paa.config`)
- `tests` contains optional directory with tests with `pytest`, copied from `tests_dir/<package_name>` (from `.paa.config`)

##### 1. Description of default tracking files

Tracking files are added automatically of artifacts adding was not turned off. At the moment contains:

- `.paa.config` : config file that specifies how paa show work
- `.paa.version`: version of `package-auto-assembler` that was used for packaging
- `release_notes.md` : latest release notes for the package
- `version_logs.csv` : logs for version updates for all packages in the packaging repo
- `lsts_package_versions.yml` : latests versions of all packages in the packaging repo
- `package_mapping.json` : additional user-provided remapping of package import names to install names
- `package_licenses.json` : additional user-provided license labels to overwrite detected ones
- `notebook.ipynb` : optional jupyter notebook that was used for package description`

##### 2. Adding files

User provided artifacts could be provided in two ways:

1. adding directory, file or link to the file under `artifacts_dir/<package_name>`

    These files would be packaged with the packages, and files from links would be downloaded and packaged as well. To add a link, create a file with `.link` extension in the name.

2. adding `artifact_urls` dictionary to `__package_metadata__` within module `.py` file

Example of `__package_metadata__` with these additional dictionary would be:

```python
__package_metadata__ = {
    ...,
    "artifact_urls" : {
        'downloaded.md' : 'https://raw.githubusercontent.com/Kiril-Mordan/reusables/refs/heads/main/docs/module_from_raw_file.md',
        'downloaded.png' : 'https://raw.githubusercontent.com/Kiril-Mordan/reusables/refs/heads/main/docs/reuse_logo.png'
    }
}
```

where key would contain name of the artifact and value its link.

These files would not be downloaded and only links would be packaged. After package installation both kinds of links could be refreshed/donwloaded using [`cli interface`](https://kiril-mordan.github.io/reusables/package_auto_assembler/cli/) from `package-auto-assembler`.

##### 3. Accessing packaged artifacts

Artifacts packaged within the package could be accessed in two ways:

1. using [`package-auto-assembler` cli tools](https://kiril-mordan.github.io/reusables/package_auto_assembler/cli_tools/#extracting-files-from-packages) to copy a file or files into a selected directory

2. reading packaged artifacts from the package, by the use of similar code that finds path to installed package in your system:

```python
import importlib
import importlib.metadata
import importlib.resources as pkg_resources

installed_package_path = pkg_resources.files('<package_name>')

file_name_path = None
if 'artifacts' in os.listdir(installed_package_path):

    with pkg_resources.path('<package_name>.artifacts', '<file_name>') as path:
        file_name_path = path
```


### 14. Preparing module for packaging

#### 1. Preparing code for packaging

To add/edit a python package with `package-auto-assembler`, its building blocks would need to follow requirements mentioned below. 

**Note**: For basic package only `main module` would be required. More about role of optional files could be seen [here](https://kiril-mordan.github.io/reusables/package_auto_assembler/python_packaging_repo/#inputs-and-outputs-of-ppr).

- Main module **[required]**

    Main module is considered to be a `<package_name>.py` file stored in `module_dir` (from `.paa.config`), which can also me called `packaging layer`. 
    This is where most code of the package would be, unless `local dependencies` are used. 

    Requirements to this file:

    1. starts with module docstring (will be used in package description)
    2. contains [`__package_metadata__`](https://kiril-mordan.github.io/reusables/package_auto_assembler/description/#4-preparing-metadata) (a way to provide package metadata)
    3. **[optional]** import from `local dependencies` stored only in `dependencies_dir`
    4. **[optional]** contains [versions of module dependencies](https://kiril-mordan.github.io/reusables/package_auto_assembler/description/#3-extracting-and-merging-requirements) (specifying requirements)


- Local dependencies

    Local dependencies are optional modules that other modules from `packaging layer` would import from, and are not packaged on their own. These are useful for segmenting codebase into smaller independent components.
    They would be stored in subdirectory of `module_dir`, specified as `dependencies_dir` in `.paa.config`. 

    Requirements for these files:

    1. stored only in `dependencies_dir` or its subdirectories 
    2. do not import any other moduled stored locally
    3. **[optional]** contain [versions of module dependencies](https://kiril-mordan.github.io/reusables/package_auto_assembler/description/#3-extracting-and-merging-requirements) (specifying requirements)


- Cli interface

    Command line interface could be optionally defined for a package by placing `<package_name>.py` file into `cli_dir` (from `.paa.config`). More about adding cli could be found [here](https://kiril-mordan.github.io/reusables/package_auto_assembler/description/#10-adding-cli-interfaces).

    Requirements for this file:

    1. imports and uses [`click`](https://pypi.org/project/click/) to define cli tools
    2. contains [`__cli_metadata__`](https://kiril-mordan.github.io/reusables/package_auto_assembler/description/#10-adding-cli-interfaces) (a way to provide alias for cli tools)
    3. **[optional]** imports from packaging layer and local dependencies only with `from <package_name>.<package_name> import ToBeImported`
    4. **[optional]** contains [versions of module dependencies](https://kiril-mordan.github.io/reusables/package_auto_assembler/description/#3-extracting-and-merging-requirements) (specifying requirements)



- API routes

    Routes for FastAPI application could be optionally defined for a package by placing `<package_name>.py` file into `api_routes_dir` (from `.paa.config`). More about adding api routes could be found [here](https://kiril-mordan.github.io/reusables/package_auto_assembler/description/#11-adding-routes-and-running-fastapi-application).

    Requirements for this file:

    1. imports `from fastapi import APIRouter`
    2. defines `router = APIRouter(prefix = "/<package-name>")`
    3. uses `@router.*` to define endpoints
    4. **[optional]** import from packaging layer and local dependencies only with `from <package_name>.<package_name> import ToBeImported`
    5. **[optional]** contain [versions of module dependencies](https://kiril-mordan.github.io/reusables/package_auto_assembler/description/#3-extracting-and-merging-requirements) (specifying requirements)


- Streamlit app

    Streamlit application could be optionally defined for a package by placing `<package_name>.py` file into `streamlit_dir` (from `.paa.config`). More about adding streamlit app could be found [here](https://kiril-mordan.github.io/reusables/package_auto_assembler/description/#12-adding-ui-and-running-streamlit-application).

    Requirements for this file:

    1. imports [`streamlit`](https://pypi.org/project/streamlit/)
    2. **[optional]** import from packaging layer and local dependencies only with `from <package_name>.<package_name> import ToBeImported`
    3. **[optional]** contain [versions of module dependencies](https://kiril-mordan.github.io/reusables/package_auto_assembler/description/#3-extracting-and-merging-requirements) (specifying requirements)



#### 2. Preparing documentation for packaging

- Package description

    Providing package description is a useful way to show what the package is about to the intended audience. By default, [`main_module`](https://kiril-mordan.github.io/reusables/package_auto_assembler/description/#preparing-code-for-packaging) docstring would be used for this purpose and stored alongside the package in a `README.md` file, as shown [here](https://kiril-mordan.github.io/reusables/package_auto_assembler/python_packaging_repo/#inputs-and-outputs-of-ppr). 

    Optionally, one could provide additional information that would be appended to the package docstring via `<package_name>.ipynb` file, placed into `example_notebooks_path` (from `.paa.config`). In the early stages of development, this file could both serve as a place where code is developed/tested before a release and a way to show usage examples.


- Additional documentation

    Package description may not be enough to store documentation. 
    A simple [mkdocs](https://www.mkdocs.org/) static site is built by default for every package with for followig tabs:

    - `intro` contains module docstring and `pypi` link for `github + pypi` type of packaging repository
    - `description` contains optional content from `<package_name>.ipynb` file, placed into `example_notebooks_path` (from `.paa.config`)
    - `release notes` contains release notes assembled based on commit messages

    Additional documentation can be provided via the following files:

    1. `<package_name>.drawio` file, placed into `drawio_dir` (from `.paa.config`). Each tab would be turned into `<package_name>-<tab_name>.png`, which if not referenced would be presented as a separate tab;
    2. `.png`, `.ipynb` or `.md` files placed in `extra_docs_dir/<package_name>` (from `.paa.config`). Each file would be turned into a separate tab, but just like `.png` from drawio, if referenced, would not be presented as a separate tab.

    **Note**: During packaging process files derived from `<package_name>.drawio` conversion and files from `extra_docs_dir/<package_name>` would both be placed into `.paa/docs` with `<package_name>-*` prefix. Make sure not to name drawio tabs and extra docs with the same names. 

#### 3. Preparing files for packaging

Packaging files alongside code and documentation could be achieved by placing files  into `artifacts_dir/<package_name>` directory (from `.paa.config`). These files could be referenced from within the package and there is an option to provide links instead of physical files. More about adding artifacts to the package could be found [here](https://kiril-mordan.github.io/reusables/package_auto_assembler/description/#13-adding-artifacts-to-packages).

Tests that would be used in ci/cd pipeline are expected to be placed into `tests_dir<package_name>` directory (from `.paa.config`). These would be copied into the package as well. 




### 15. Making a package

Main wrapper for the package integrates described above components into a class that could be used to build package building pipelines within python scripts. 

To simplify usage [cli interface](https://kiril-mordan.github.io/reusables/package_auto_assembler/cli/) is recomended instead. 

---

initializing PackageAutoAssembler


```python
paa = PackageAutoAssembler(
    # required
    module_name = "example_module",
    module_filepath  = "../tests/package_auto_assembler/other/example_module.py",
    # optional
    mapping_filepath = "../env_spec/package_mapping.json",
    licenses_filepath = "../tests/package_auto_assembler/other/package_licenses.json",
    allowed_licenses = ['mit', 'apache-2.0', 'lgpl-3.0', 'mpl-2.0', '-'],
    dependencies_dir = "../tests/package_auto_assembler/dependancies/",
    example_notebook_path = "./mock_vector_database.ipynb",
    versions_filepath = '../tests/package_auto_assembler/other/lsts_package_versions.yml',
    log_filepath = '../tests/package_auto_assembler/other/version_logs.csv',
    setup_directory = "./example_module",
    release_notes_filepath = "../tests/package_auto_assembler/other/release_notes.md",
    license_path = "../LICENSE",
    license_label = "mit",
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
    default_version = "0.0.1",
    check_vulnerabilities = True,
    check_dependencies_licenses = False,
    add_requirements_header = True
)
```

add metadata from module


```python
paa.add_metadata_from_module(
    # optional
    module_filepath  = "../tests/package_auto_assembler/other/example_module.py"
)
```

    Adding metadata ...


add or update version


```python
paa.add_or_update_version(
    # overwrites auto mode (not suggested)
    version_increment_type = "patch",
    version = "1.2.6",
    # optional
    module_name = "example_module",
    versions_filepath = '../tests/package_auto_assembler/lsts_package_versions.yml',
    log_filepath = '../tests/package_auto_assembler/version_logs.csv'
)
```

    Incrementing version ...
    No relevant commit messages found!
    ..trying depth 2 !
    No relevant commit messages found!
    ..trying depth 3 !
    No relevant commit messages found!
    ..trying depth 4 !
    No relevant commit messages found!
    ..trying depth 5 !
    No relevant commit messages found!
    No messages to clean were provided


add release notes from commit messages


```python
paa.add_or_update_release_notes(
    # optional
    filepath="../tests/package_auto_assembler/release_notes.md",
    version=paa.metadata['version']
)
```

    Updating release notes ...


prepare setup directory


```python
paa.prep_setup_dir()
```

    Preparing setup directory ...


merge local dependacies


```python
paa.merge_local_dependacies(
    # optional
    main_module_filepath = "../tests/package_auto_assembler/other/example_module.py",
    dependencies_dir= "../tests/package_auto_assembler/dependancies/",
    save_filepath = "./example_module/example_module.py"
)
```

    Merging ../tests/package_auto_assembler/other/example_module.py with dependecies from ../tests/package_auto_assembler/dependancies/ into ./example_module/example_module.py


add requirements from module


```python
paa.add_requirements_from_module(
    # optional
    module_filepath = "../tests/package_auto_assembler/other/example_module.py",
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
                        'yaml': 'pyyaml',
                        'git' : 'gitpython'}
)
```

    Adding requirements from ../tests/package_auto_assembler/other/example_module.py
    No known vulnerabilities found
    


    



```python
paa.requirements_list
```




    ['### example_module.py', 'attrs>=22.2.0']



make README out of example notebook


```python
paa.add_readme(
    # optional
    example_notebook_path = "../tests/package_auto_assembler/other/example_module.ipynb",
    output_path = "./example_module/README.md",
    execute_notebook=False,
)
```

    Adding README from ../tests/package_auto_assembler/other/example_module.ipynb to ./example_module/README.md


prepare setup file


```python
paa.prep_setup_file(
    # optional
    metadata = {'author': 'Kyrylo Mordan',
                'version': '0.0.1',
                'description': 'Example module',
                'keywords': ['python'],
                'license' : 'mit'},
    requirements = ['### example_module.py',
                    'attrs>=22.2.0'],
    classifiers = ['Development Status :: 3 - Alpha',
                    'Intended Audience :: Developers',
                    'Intended Audience :: Science/Research',
                    'Programming Language :: Python :: 3',
                    'Programming Language :: Python :: 3.9',
                    'Programming Language :: Python :: 3.10',
                    'Programming Language :: Python :: 3.11',
                    'License :: OSI Approved :: MIT License',
                    'Topic :: Scientific/Engineering'],
    cli_module_filepath = "../tests/package_auto_assembler/other/cli.py"

)
```

    Preparing setup file for example-module package ...


make package


```python
paa.make_package(
    # optional
    setup_directory = "./example_module"
)
```

    Making package from ./example_module ...





    CompletedProcess(args=['python', './example_module/setup.py', 'sdist', 'bdist_wheel'], returncode=0, stdout="running sdist\nrunning egg_info\nwriting example_module.egg-info/PKG-INFO\nwriting dependency_links to example_module.egg-info/dependency_links.txt\nwriting entry points to example_module.egg-info/entry_points.txt\nwriting requirements to example_module.egg-info/requires.txt\nwriting top-level names to example_module.egg-info/top_level.txt\nreading manifest file 'example_module.egg-info/SOURCES.txt'\nwriting manifest file 'example_module.egg-info/SOURCES.txt'\nrunning check\ncreating example_module-0.0.0\ncreating example_module-0.0.0/example_module\ncreating example_module-0.0.0/example_module.egg-info\ncopying files to example_module-0.0.0...\ncopying example_module/__init__.py -> example_module-0.0.0/example_module\ncopying example_module/cli.py -> example_module-0.0.0/example_module\ncopying example_module/example_module.py -> example_module-0.0.0/example_module\ncopying example_module/setup.py -> example_module-0.0.0/example_module\ncopying example_module.egg-info/PKG-INFO -> example_module-0.0.0/example_module.egg-info\ncopying example_module.egg-info/SOURCES.txt -> example_module-0.0.0/example_module.egg-info\ncopying example_module.egg-info/dependency_links.txt -> example_module-0.0.0/example_module.egg-info\ncopying example_module.egg-info/entry_points.txt -> example_module-0.0.0/example_module.egg-info\ncopying example_module.egg-info/requires.txt -> example_module-0.0.0/example_module.egg-info\ncopying example_module.egg-info/top_level.txt -> example_module-0.0.0/example_module.egg-info\ncopying example_module.egg-info/SOURCES.txt -> example_module-0.0.0/example_module.egg-info\nWriting example_module-0.0.0/setup.cfg\nCreating tar archive\nremoving 'example_module-0.0.0' (and everything under it)\nrunning bdist_wheel\nrunning build\nrunning build_py\ncopying example_module/example_module.py -> build/lib/example_module\ncopying example_module/__init__.py -> build/lib/example_module\ncopying example_module/setup.py -> build/lib/example_module\ncopying example_module/cli.py -> build/lib/example_module\ninstalling to build/bdist.linux-x86_64/wheel\nrunning install\nrunning install_lib\ncreating build/bdist.linux-x86_64/wheel\ncreating build/bdist.linux-x86_64/wheel/example_module\ncopying build/lib/example_module/example_module.py -> build/bdist.linux-x86_64/wheel/example_module\ncopying build/lib/example_module/__init__.py -> build/bdist.linux-x86_64/wheel/example_module\ncopying build/lib/example_module/setup.py -> build/bdist.linux-x86_64/wheel/example_module\ncopying build/lib/example_module/cli.py -> build/bdist.linux-x86_64/wheel/example_module\nrunning install_egg_info\nCopying example_module.egg-info to build/bdist.linux-x86_64/wheel/example_module-0.0.0-py3.10.egg-info\nrunning install_scripts\ncreating build/bdist.linux-x86_64/wheel/example_module-0.0.0.dist-info/WHEEL\ncreating 'dist/example_module-0.0.0-py3-none-any.whl' and adding 'build/bdist.linux-x86_64/wheel' to it\nadding 'example_module/__init__.py'\nadding 'example_module/cli.py'\nadding 'example_module/example_module.py'\nadding 'example_module/setup.py'\nadding 'example_module-0.0.0.dist-info/METADATA'\nadding 'example_module-0.0.0.dist-info/WHEEL'\nadding 'example_module-0.0.0.dist-info/entry_points.txt'\nadding 'example_module-0.0.0.dist-info/top_level.txt'\nadding 'example_module-0.0.0.dist-info/RECORD'\nremoving build/bdist.linux-x86_64/wheel\n", stderr='warning: sdist: standard file not found: should have one of README, README.rst, README.txt, README.md\n\n/home/kyriosskia/miniconda3/envs/testenv/lib/python3.10/site-packages/setuptools/_distutils/cmd.py:66: SetuptoolsDeprecationWarning: setup.py install is deprecated.\n!!\n\n        ********************************************************************************\n        Please avoid running ``setup.py`` directly.\n        Instead, use pypa/build, pypa/installer or other\n        standards-based tools.\n\n        See https://blog.ganssle.io/articles/2021/10/setup-py-deprecated.html for details.\n        ********************************************************************************\n\n!!\n  self.initialize_options()\n')



### 16. Making simple MkDocs site

Package documentation can be presented in a form of mkdocs static site, which could be either served or deployed to something like github packages. 

Main module docstring is used as intro package that contains something like optional pypi and license badges. Package description and realease notes are turned into separate tabs. Png with diagrams for example could be provided and displayed as their own separate tabs as well.
 
The one for this package can be seen [here](https://kiril-mordan.github.io/reusables/package_auto_assembler/)

It can be packaged with the package and be displayed in web browser like documentation for api via `<package-name>\docs` when using included api handling capabilities.

---

##### 1. Preparing inputs


```python
package_name = "example_module"

module_content = LongDocHandler().read_module_content(filepath=f"../tests/package_auto_assembler/{package_name}.py")

docstring = LongDocHandler().extract_module_docstring(module_content=module_content)
pypi_link = LongDocHandler().get_pypi_badge(module_name=package_name)


docs_file_paths = {
    "../example_module.md" : "usage-examples.md",
    '../tests/package_auto_assembler/release_notes.md' : 'release_notes.md'
}
```


```python
mdh = MkDocsHandler(
    # required
    ## name of the package to be displayed
    package_name = package_name,
    ## dictionary of markdown files, with path as keys
    docs_file_paths = docs_file_paths,
    # optional
    ## module docstring to be displayed in the index
    module_docstring = docstring,
    ## pypi badge to be displayed in the index
    pypi_badge = pypi_link,
    ## license badge to be displayed in the index
    license_badge="[![License](https://img.shields.io/github/license/Kiril-Mordan/reusables)](https://github.com/Kiril-Mordan/reusables/blob/main/LICENSE)",
    ## name of the project directory
    project_name = "temp_project")
```

##### 2. Preparing site


```python
mdh.create_mkdocs_dir()
mdh.move_files_to_docs()
mdh.generate_markdown_for_images()
mdh.create_index()
mdh.create_mkdocs_yml()
mdh.build_mkdocs_site()
```

    Created new MkDocs dir: temp_project
    Copied ../example_module.md to temp_project/docs/usage-examples.md
    Copied ../tests/package_auto_assembler/release_notes.md to temp_project/docs/release_notes.md
    index.md has been created with site_name: example-module
    mkdocs.yml has been created with site_name: Example module
    Custom CSS created at temp_project/docs/css/extra.css


    INFO    -  Cleaning site directory
    INFO    -  Building documentation to directory: /home/kyriosskia/Documents/nlp/reusables/example_notebooks/temp_project/site
    INFO    -  Documentation built in 0.12 seconds


##### 3. Test-running site


```python
mdh.serve_mkdocs_site()
```
