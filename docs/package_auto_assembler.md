```python
import sys
sys.path.append('../')
from python_modules.package_auto_assembler import (VersionHandler, \
    ImportMappingHandler, RequirementsHandler, MetadataHandler, \
        LocalDependaciesHandler, LongDocHandler, SetupDirHandler, \
            ReleaseNotesHandler, MkDocsHandler, PackageAutoAssembler)
```

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
      <td>2024-05-28 01:28:20</td>
      <td>new_package</td>
      <td>0.0.1</td>
    </tr>
    <tr>
      <th>2</th>
      <td>2024-05-28 01:28:20</td>
      <td>new_package</td>
      <td>0.0.2</td>
    </tr>
    <tr>
      <th>3</th>
      <td>2024-05-28 01:28:20</td>
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



#### Audit dependencies


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
    
    # Metadata for package creation
    
    
    @attr.s
    class ComparisonFrame:
    
        """
        Compares query:response pairs expected vs recieved with semantic similarity
        and simple metrics of word count, line count etc.
    
        ...
    
        Attributes
        ----------
        embedder : SentenceTransformer
            The model used to generate embeddings for semantic comparison.
        record_file : str
            The name of the CSV file where queries and expected results are stored.
        results_file : str
            The name of the CSV file where comparison results 



```python
ldh.dependencies_names_list
```




    ['example_local_dependacy_1', 'example_local_dependacy_2']



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
    default_version = "0.0.1",
    check_vulnerabilities = True
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

    No known vulnerabilities found
    


    



```python
paa.requirements_list
```




    ['### example_module.py', 'attrs>=22.2.0']



#### Make README out of example notebook


```python
paa.add_readme(
    # optional
    example_notebook_path = "../tests/package_auto_assembler/example_module.ipynb",
    output_path = "./example_module/README.md",
    execute_notebook=False,
)
```

#### Prepare setup file


```python
paa.prep_setup_file(
    # optional
    metadata = {'author': 'Kyrylo Mordan',
                'version': '0.0.1',
                'description': 'Example module',
                'keywords': ['python']},
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
    cli_module_filepath = "../tests/package_auto_assembler/cli.py"

)
```

#### Make package


```python
paa.make_package(
    # optional
    setup_directory = "./example_module"
)
```




    CompletedProcess(args=['python', './example_module/setup.py', 'sdist', 'bdist_wheel'], returncode=0, stdout="running sdist\nrunning egg_info\nwriting example_module.egg-info/PKG-INFO\nwriting dependency_links to example_module.egg-info/dependency_links.txt\nwriting entry points to example_module.egg-info/entry_points.txt\nwriting requirements to example_module.egg-info/requires.txt\nwriting top-level names to example_module.egg-info/top_level.txt\nreading manifest file 'example_module.egg-info/SOURCES.txt'\nwriting manifest file 'example_module.egg-info/SOURCES.txt'\nrunning check\ncreating example_module-0.0.1\ncreating example_module-0.0.1/example_module\ncreating example_module-0.0.1/example_module.egg-info\ncopying files to example_module-0.0.1...\ncopying example_module/__init__.py -> example_module-0.0.1/example_module\ncopying example_module/cli.py -> example_module-0.0.1/example_module\ncopying example_module/example_module.py -> example_module-0.0.1/example_module\ncopying example_module/setup.py -> example_module-0.0.1/example_module\ncopying example_module.egg-info/PKG-INFO -> example_module-0.0.1/example_module.egg-info\ncopying example_module.egg-info/SOURCES.txt -> example_module-0.0.1/example_module.egg-info\ncopying example_module.egg-info/dependency_links.txt -> example_module-0.0.1/example_module.egg-info\ncopying example_module.egg-info/entry_points.txt -> example_module-0.0.1/example_module.egg-info\ncopying example_module.egg-info/requires.txt -> example_module-0.0.1/example_module.egg-info\ncopying example_module.egg-info/top_level.txt -> example_module-0.0.1/example_module.egg-info\ncopying example_module.egg-info/SOURCES.txt -> example_module-0.0.1/example_module.egg-info\nWriting example_module-0.0.1/setup.cfg\ncreating dist\nCreating tar archive\nremoving 'example_module-0.0.1' (and everything under it)\nrunning bdist_wheel\nrunning build\nrunning build_py\ncopying example_module/example_module.py -> build/lib/example_module\ncopying example_module/__init__.py -> build/lib/example_module\ncopying example_module/setup.py -> build/lib/example_module\ncopying example_module/cli.py -> build/lib/example_module\ninstalling to build/bdist.macosx-10.9-x86_64/wheel\nrunning install\nrunning install_lib\ncreating build/bdist.macosx-10.9-x86_64/wheel\ncreating build/bdist.macosx-10.9-x86_64/wheel/example_module\ncopying build/lib/example_module/example_module.py -> build/bdist.macosx-10.9-x86_64/wheel/example_module\ncopying build/lib/example_module/__init__.py -> build/bdist.macosx-10.9-x86_64/wheel/example_module\ncopying build/lib/example_module/setup.py -> build/bdist.macosx-10.9-x86_64/wheel/example_module\ncopying build/lib/example_module/cli.py -> build/bdist.macosx-10.9-x86_64/wheel/example_module\nrunning install_egg_info\nCopying example_module.egg-info to build/bdist.macosx-10.9-x86_64/wheel/example_module-0.0.1-py3.9.egg-info\nrunning install_scripts\ncreating build/bdist.macosx-10.9-x86_64/wheel/example_module-0.0.1.dist-info/WHEEL\ncreating 'dist/example_module-0.0.1-py3-none-any.whl' and adding 'build/bdist.macosx-10.9-x86_64/wheel' to it\nadding 'example_module/__init__.py'\nadding 'example_module/cli.py'\nadding 'example_module/example_module.py'\nadding 'example_module/setup.py'\nadding 'example_module-0.0.1.dist-info/METADATA'\nadding 'example_module-0.0.1.dist-info/WHEEL'\nadding 'example_module-0.0.1.dist-info/entry_points.txt'\nadding 'example_module-0.0.1.dist-info/top_level.txt'\nadding 'example_module-0.0.1.dist-info/RECORD'\nremoving build/bdist.macosx-10.9-x86_64/wheel\n", stderr='warning: sdist: standard file not found: should have one of README, README.rst, README.txt, README.md\n\n/Users/insani_dei/miniconda3/envs/testenv/lib/python3.9/site-packages/setuptools/_distutils/cmd.py:66: SetuptoolsDeprecationWarning: setup.py install is deprecated.\n!!\n\n        ********************************************************************************\n        Please avoid running ``setup.py`` directly.\n        Instead, use pypa/build, pypa/installer or other\n        standards-based tools.\n\n        See https://blog.ganssle.io/articles/2021/10/setup-py-deprecated.html for details.\n        ********************************************************************************\n\n!!\n  self.initialize_options()\n')



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


##### - overwritting commit messages from example


```python
# commit messages from last merge
rnh.commit_messages
```




    ['slight changes to gh-pages workflow',
     'adding package_auto_assembler to usage examples test run exceptions',
     'updated gh-pages workflow',
     'testing newer MkDocsHandler',
     'updated workflows',
     'package name parameter for gh-pages workflow']




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
    ['# Release notes\n', '\n', '### 0.0.2\n', '\n', '    - usage example for initial release notes\n', '\n', '    - bugfixes for RNH\n', '\n', '    - initial release notes handler\n', '\n', '### 0.0.1\n', '\n', '    - initial version of example_module\n']


##### - saving updated relese notes


```python
rnh.existing_contents
```




    ['# Release notes\n',
     '\n',
     '### 0.0.1\n',
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
     '\n',
     '    - bugfixes for RNH\n',
     '\n',
     '    - initial release notes handler\n',
     '\n',
     '### 0.0.1\n',
     '\n',
     '    - initial version of example_module\n']



### 10. Making simple MkDocs site

##### - preparing inputs


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

##### - preparing site


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
    INFO    -  Building documentation to directory: /Users/user/reusables/example_notebooks/temp_project/site
    INFO    -  Documentation built in 0.80 seconds


##### - test runing site


```python
mdh.serve_mkdocs_site()
```
