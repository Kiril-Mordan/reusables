"""
Package Auto Assembler

This tool is meant to streamline creation of single module packages.
Its purpose is to automate as many aspects of python package creation as possible,
to shorten a development cycle of reusable components, maintain certain standard of quality
for reusable code. It provides tool to simplify the process of package creatrion
to a point that it can be triggered automatically within ci/cd pipelines,
with minimal preparations and requirements for new modules.
"""

# Imports
## essential
import logging
import os
import attr
## working with files
import pandas as pd
import yaml
import json
import csv
## other
from datetime import datetime
import re
import importlib.util
from stdlib_list import stdlib_list
import subprocess
import shutil



@attr.s
class VersionHandler:

    versions_filepath = attr.ib()
    log_filepath = attr.ib()

    default_version = attr.ib(default="0.0.1")

    logger = attr.ib(default=None)
    logger_name = attr.ib(default='Package Version Handler')
    loggerLvl = attr.ib(default=logging.INFO)
    logger_format = attr.ib(default=None)

    def __attrs_post_init__(self):
        self._initialize_logger()
        try:
            self.versions = self._read_versions()
        except Exception as e:
            self._create_versions()
            self.versions = {}
        self._setup_logging()


    def _initialize_logger(self):

        """
        Initialize a logger for the class instance based on the specified logging level and logger name.
        """

        if self.logger is None:
            logging.basicConfig(level=self.loggerLvl, format=self.logger_format)
            logger = logging.getLogger(self.logger_name)
            logger.setLevel(self.loggerLvl)

            self.logger = logger

    def _setup_logging(self):
        self.log_file = open(self.log_filepath, 'a', newline='')
        self.csv_writer = csv.writer(self.log_file)
        # Write headers if the file is empty/new
        if os.stat(self.log_filepath).st_size == 0:
            self.csv_writer.writerow(['Timestamp', 'Package', 'Version'])

    def _read_versions(self):
        with open(self.versions_filepath, 'r') as file:
            return yaml.safe_load(file) or {}

    def _create_versions(self):
        self.logger.debug(f"Versions file was not found in location '{self.versions_filepath}', creating file!")
        with open(self.versions_filepath, 'w') as file:
            pass

    def _save_versions(self):
        with open(self.versions_filepath, 'w') as file:
            yaml.safe_dump(self.versions, file)

    def __str__(self):
        return yaml.safe_dump(self.versions)

    def _parse_version(self, version):
        major, minor, patch = map(int, version.split('.'))
        return major, minor, patch

    def _format_version(self, major, minor, patch):
        return f"{major}.{minor}.{patch}"

    def flush_versions(self):
        with open(self.versions_filepath, 'w') as file:
            yaml.safe_dump({}, file)

    def flush_logs(self):
        # Close connection
        self._close_log_file()
        # Open the file in write mode to clear it, then write back only the headers
        with open(self.log_filepath, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Timestamp', 'Package', 'Version'])  # column headers
        # Reopen connection
        self._setup_logging()


    def log_version_update(self, package_name, new_version):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.csv_writer.writerow([timestamp, package_name, new_version])
        self.log_file.flush()  # Ensure data is written to the file
        self._close_log_file()
        self._setup_logging()

    def get_logs(self,
                 log_filepath : str = None):

        if log_filepath is None:
            log_filepath = self.log_filepath

        return(pd.read_csv(log_filepath))

    def get_version(self, package_name : str = None):

        return self.versions.get(package_name)

    def get_versions(self,
                     versions_filepath : str = None):

        if versions_filepath is None:
            versions_filepath = self.versions_filepath

        # Open the YAML file
        with open(versions_filepath, 'r') as file:
            # Load the contents of the file
            versions = yaml.safe_load(file)


        return(versions)

    # Remember to close the log file when done
    def _close_log_file(self):
        self.log_file.close()


    def update_version(self, package_name, new_version):
        self.versions[package_name] = new_version
        self._save_versions()
        self.log_version_update(package_name, new_version)

    def add_package(self,
                    package_name : str,
                    version : str = None):

        if version is None:
            version = self.default_version

        if package_name not in self.versions:
            self.versions[package_name] = version
            self._save_versions()
            self.log_version_update(package_name, version)



    def increment_version(self,
                          package_name : str,
                          type : str = None,
                          default_version : str = None):

        if default_version is None:
            default_version = self.default_version

        if type is None:
            type = 'patch'

        if package_name in self.versions:
            prev_version = self.versions[package_name]
            major, minor, patch = self._parse_version(prev_version)

            if type == 'patch':
                patch += 1
            if type == 'minor':
                minor += 1
            if type == 'major':
                major += 1

            new_version = self._format_version(major, minor, patch)
            self.update_version(package_name, new_version)

            self.logger.debug(f"Incremented {type} of {package_name} \
                from {prev_version} to {new_version}")
        else:
            self.logger.warning(f"There are no known versions of '{package_name}', {default_version} will be used!")
            self.update_version(package_name, default_version)



    def increment_major(self,
                        package_name : str,
                        default_version : str = None):

        if default_version is None:
            default_version = self.default_version

        self.increment_version(package_name = package_name,
                             default_version = default_version,
                             type = 'major')

    def increment_minor(self,
                        package_name : str,
                        default_version : str = None):

        if default_version is None:
            default_version = self.default_version

        self.increment_version(package_name = package_name,
                             default_version = default_version,
                             type = 'minor')

    def increment_patch(self,
                        package_name : str,
                        default_version : str = None):

        if default_version is None:
            default_version = self.default_version

        self.increment_version(package_name = package_name,
                             default_version = default_version,
                             type = 'patch')

@attr.s
class ImportMappingHandler:

    mapping_filepath = attr.ib()

    logger = attr.ib(default=None)
    logger_name = attr.ib(default='Package Import Mapping Handler')
    loggerLvl = attr.ib(default=logging.INFO)
    logger_format = attr.ib(default=None)

    def __attrs_post_init__(self):
        self._initialize_logger()

    def _initialize_logger(self):

        """
        Initialize a logger for the class instance based on the specified logging level and logger name.
        """

        if self.logger is None:
            logging.basicConfig(level=self.loggerLvl, format=self.logger_format)
            logger = logging.getLogger(self.logger_name)
            logger.setLevel(self.loggerLvl)

            self.logger = logger


    def load_package_mappings(self,
                              mapping_filepath : str = None):
        """
        Get file with mappings for packages which import names differ from install names.
        """

        if mapping_filepath is None:
            mapping_filepath = self.mapping_filepath

        with open(mapping_filepath, 'r') as file:
            return json.load(file)

@attr.s
class LocalDependaciesHandler:

    main_module_filepath = attr.ib()
    dependencies_dir = attr.ib()


    def read_module(self,
                    filepath : str = None) -> str:

        if filepath is None:
            filepath = self.main_module_filepath

        with open(filepath, 'r') as file:
            return file.read()

    def extract_module_docstring(self,
                                 module_content : str) -> str:

        match = re.match(r'(""".*?"""|\'\'\'.*?\'\'\')', module_content, re.DOTALL)
        return match.group(0) if match else ''

    def extract_imports(self,
                        module_content : str) -> str:

        return re.findall(r'^(?:from\s+.+\s+)?import\s+.+$', module_content, re.MULTILINE)


    def remove_module_docstring(self,
                                module_content : str) -> str:

        return re.sub(r'^(""".*?"""|\'\'\'.*?\'\'\')', '', module_content, flags=re.DOTALL).strip()

    def remove_imports(self,
                       module_content : str) -> str:

        module_content = re.sub(r'^(?:from\s+.+\s+)?import\s+.+$', '', module_content, flags=re.MULTILINE)
        return module_content.strip()

    def combine_modules(self,
                        main_module_path : str = None,
                        dependencies_dir : str = None) -> str:

        if main_module_path is None:
            main_module_path = self.main_module_filepath

        if dependencies_dir is None:
            dependencies_dir = self.dependencies_dir


        # Read main module
        main_module_content = self.read_module(main_module_path)

        # Extract and preserve the main module's docstring and imports
        main_module_docstring = self.extract_module_docstring(main_module_content)
        main_module_imports = self.extract_imports(main_module_content)

        # List of dependency module names
        dependencies = [os.path.splitext(f)[0] for f in os.listdir(dependencies_dir) if f.endswith('.py')]

        # Remove specific dependency imports from the main module
        for dep in dependencies:
            main_module_imports = [imp for imp in main_module_imports if f'.{dep} import *' not in imp]
        main_module_content = self.remove_imports(main_module_content)

        # Process dependency modules
        combined_content = ""
        for filename in dependencies:
            dep_content = self.read_module(os.path.join(dependencies_dir, f"{filename}.py"))
            dep_content = self.remove_module_docstring(dep_content)
            dep_imports = self.extract_imports(dep_content)
            main_module_imports.extend(dep_imports)
            combined_content += self.remove_module_docstring(self.remove_imports(dep_content)) + "\n\n"

        # Combine everything
        unique_imports = sorted(set(main_module_imports), key=lambda x: main_module_imports.index(x))
        combined_module = main_module_docstring + "\n\n" + '\n'.join(unique_imports) + "\n\n" + combined_content + main_module_content
        return combined_module


@attr.s
class RequirementsHandler:

    custom_modules_filepath = attr.ib()
    python_version = attr.ib(default='3.8')

    logger = attr.ib(default=None)
    logger_name = attr.ib(default='Package Requirements Handler')
    loggerLvl = attr.ib(default=logging.INFO)
    logger_format = attr.ib(default=None)

    def __attrs_post_init__(self):
        self._initialize_logger()


    def _initialize_logger(self):

        """
        Initialize a logger for the class instance based on the specified logging level and logger name.
        """

        if self.logger is None:
            logging.basicConfig(level=self.loggerLvl, format=self.logger_format)
            logger = logging.getLogger(self.logger_name)
            logger.setLevel(self.loggerLvl)

            self.logger = logger


    def list_custom_modules(self,
                            custom_modules_filepath : str = None):
        """
        List all custom module names in the specified directory.
        """

        if custom_modules_filepath is None:
            custom_modules_filepath = self.custom_modules_filepath

        custom_modules = set()
        for filename in os.listdir(custom_modules_filepath):
            if filename.endswith('.py') and not filename.startswith('__'):
                module_name = filename.rsplit('.', 1)[0]
                custom_modules.add(module_name)
        return custom_modules

    def is_standard_library(self,
                            module_name : str,
                            python_version : str = None):

        """
        Check if a module is part of the standard library for the given Python version.
        """

        if python_version is None:
            python_version = self.python_version

        return module_name in stdlib_list(python_version)


    def read_requirements_file(self,
                               filename):
        with open(filename, 'r') as file:
            return [line.strip() for line in file if line.strip() and not line.startswith('#')]

    def extract_requirements(self,
                             path_to_module,
                             module_name,
                             custom_modules,
                             package_mappings = {},
                             python_version='3.8'):

        file_path = f"{path_to_module}/{module_name}.py"

        # Separate regex patterns for 'import' and 'from ... import ...' statements
        import_pattern = re.compile(r"import (\S+)(?:\s+#(?:\s*(==|>=|<=|>|<)\s*([0-9.]+)))?")
        from_import_pattern = re.compile(r"from (\S+) import.*(?:\s+#(?:\s*(==|>=|<=|>|<)\s*([0-9.]+)))?")

        requirements = [f'### {module_name}']

        with open(file_path, 'r') as file:
            for line in file:
                import_match = import_pattern.match(line)
                from_import_match = from_import_pattern.match(line)

                if import_match:
                    module, version_constraint, version = import_match.groups()
                elif from_import_match:
                    module, version_constraint, version = from_import_match.groups()
                else:
                    continue

                # Extract the base package name
                module = module.split('.')[0]

                # Skip standard library and custom modules
                if self.is_standard_library(module, python_version) or module in custom_modules or module == path_to_module:
                    continue

                # Use the mapping to get the correct package name
                module = package_mappings.get(module, module)

                version_info = f"{version_constraint}{version}" if version_constraint and version else ""

                # Print for debugging
                # print(f"Matched line: {line.strip()}, Module: {module}, Version: {version_info}")

                if version_info:
                    requirements.append(f"{module}{version_info}")
                else:
                    requirements.append(module)

        return requirements

    def write_requirements_file(self,
                                requirements,
                                module_name,
                                output_path,
                                prefix = "requirements_"):

        output_file = f"{output_path}/{prefix}{module_name}.txt"

        with open(output_file, 'w') as file:
            for req in requirements:
                file.write(req + '\n')

@attr.s
class MetadataHandler:


    module_filepath = attr.ib()

    logger = attr.ib(default=None)
    logger_name = attr.ib(default='Package Metadata Handler')
    loggerLvl = attr.ib(default=logging.INFO)
    logger_format = attr.ib(default=None)

    def __attrs_post_init__(self):
        self._initialize_logger()


    def _initialize_logger(self):

        """
        Initialize a logger for the class instance based on the specified logging level and logger name.
        """

        if self.logger is None:
            logging.basicConfig(level=self.loggerLvl, format=self.logger_format)
            logger = logging.getLogger(self.logger_name)
            logger.setLevel(self.loggerLvl)

            self.logger = logger

    # check if metadata is available
    def get_package_metadata(self, module_filepath : str = None):

        if module_filepath is None:
            module_filepath = self.module_filepath

        module_name =  os.path.basename(module_filepath)
        spec = importlib.util.spec_from_file_location(module_name, module_filepath)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.__package_metadata__


@attr.s
class SetupDirHandler:

    module_filepath = attr.ib(type=str)
    module_name = attr.ib(default='', type=str)
    metadata = attr.ib(default={}, type=dict)
    requirements = attr.ib(default='', type=str)
    classifiers = attr.ib(default=[], type=list)
    setup_directory = attr.ib(default='./setup_dir')

    logger = attr.ib(default=None)
    logger_name = attr.ib(default='Package Setup Dir Handler')
    loggerLvl = attr.ib(default=logging.INFO)
    logger_format = attr.ib(default=None)

    def __attrs_post_init__(self):
        self._initialize_logger()


    def _initialize_logger(self):

        """
        Initialize a logger for the class instance based on the specified logging level and logger name.
        """

        if self.logger is None:
            logging.basicConfig(level=self.loggerLvl, format=self.logger_format)
            logger = logging.getLogger(self.logger_name)
            logger.setLevel(self.loggerLvl)

            self.logger = logger

    def flush_n_make_setup_dir(self,
                               setup_directory : str = None):

        if setup_directory is None:
            setup_directory = self.setup_directory

        # Flushing setup directory
        if os.path.exists(setup_directory):
            shutil.rmtree(setup_directory)
        os.makedirs(setup_directory)


    def copy_module_to_setup_dir(self,
                                 module_filepath : str = None,
                                 setup_directory : str = None):


        if module_filepath is None:
            module_filepath = self.module_filepath

        if setup_directory is None:
            setup_directory = self.setup_directory

        # Copying module to setup directory
        shutil.copy(module_filepath, setup_directory)


    def create_init_file(self,
                         module_name : str = None,
                         setup_directory : str = None):

        if module_name is None:
            if self.module_name == '':
                module_name = os.path.basename(self.module_filepath)
            else:
                module_name = self.module_name

        if setup_directory is None:
            setup_directory = self.setup_directory

        # Creating temporary __init__.py file
        init_file_path = os.path.join(setup_directory, '__init__.py')
        with open(init_file_path, 'w') as init_file:
            init_file.write(f"from .{module_name} import *\n")

    def write_setup_file(self,
                         module_name : str = None,
                         metadata : dict = None,
                         requirements : str = None,
                         classifiers : list = None,
                         setup_directory : str = None):

        if module_name is None:
            if self.module_name == '':
                module_name = os.path.basename(self.module_filepath)
            else:
                module_name = self.module_name

        if metadata is None:
            metadata = self.metadata

        if requirements is None:
            requirements = self.requirements

        if classifiers is None:
            classifiers = self.classifiers

        if setup_directory is None:
            setup_directory = self.setup_directory

        metadata_str = ', '.join([f'{key}="{value}"' for key, value in metadata.items()])
        setup_content = f"""from setuptools import setup

    setup(
        name="{module_name}",
        packages=["{module_name}"],
        install_requires={requirements},
        classifiers={classifiers},
        {metadata_str}
    )
        """
        with open('setup_dir/setup.py', 'w') as file:
            file.write(setup_content)


    # def prep_module_setup_dir(self, module_file, modules_directory, setup_directory):
    #     module_name = os.path.splitext(os.path.basename(module_file))[0]
    #     print(f"Preparing dir structure for module: {module_name}")

    #     # Flushing setup directory
    #     if os.path.exists(setup_directory):
    #         shutil.rmtree(setup_directory)
    #     os.makedirs(setup_directory)

    #     # Copying module to setup directory
    #     shutil.copy(os.path.join(modules_directory, module_file), setup_directory)

    #     # Creating temporary __init__.py file
    #     init_file_path = os.path.join(setup_directory, '__init__.py')
    #     with open(init_file_path, 'w') as init_file:
    #         init_file.write(f"from .{module_name} import *\n")


@attr.s
class PackageAutoAssembler:
    # pylint: disable=too-many-instance-attributes

    ## inputs
    module_name = attr.ib(type=str)

    ## paths
    module_filepath  = attr.ib(type=str)
    versions_filepath = attr.ib(default='./lsts_package_versions.yml')
    log_filepath = attr.ib(default='./version_logs.csv')
    setup_directory = attr.ib(default='./setup_dir')

    ## handlers
    setup_dir_h = attr.ib(default=SetupDirHandler)
    version_h = attr.ib(default=VersionHandler)
    import_mapping_h = attr.ib(default=ImportMappingHandler)
    local_dependacies_h = attr.ib(default=LocalDependaciesHandler)
    requirements_h = attr.ib(default=RequirementsHandler)
    metadata_h = attr.ib(default=MetadataHandler)

    ## output
    package_result = attr.ib(init=False)
    metadata = attr.ib(init=False)

    logger = attr.ib(default=None)
    logger_name = attr.ib(default='Package Auto Assembler')
    loggerLvl = attr.ib(default=logging.INFO)
    logger_format = attr.ib(default=None)

    def __attrs_post_init__(self):
        self._initialize_logger()
        self._initialize_handlers()


    def _initialize_logger(self):

        """
        Initialize a logger for the class instance based on the specified logging level and logger name.
        """

        if self.logger is None:
            logging.basicConfig(level=self.loggerLvl, format=self.logger_format)
            logger = logging.getLogger(self.logger_name)
            logger.setLevel(self.loggerLvl)

            self.logger = logger

    def _initialize_handlers(self):

        """
        Initialize handlers with available parameters.
        """

        self.setup_dir_h(module_name = self.module_name,
                         module_filepath = self.module_filepath,
                         logger = self.logger)

        self.metadata_h(module_filepath = self.module_filepath)

    def add_or_update_version(self,
                              version : str = None,
                              versions_filepath : str = None,
                              log_filepath : str = None):

        if versions_filepath is None:
            versions_filepath = self.versions_filepath

        if log_filepath is None:
            log_filepath = self.log_filepath

    def prep_metadata(self, module_filepath : str = None):

        if module_filepath is None:
            module_filepath = self,module_filepath

        # extracting package metadata
        self.metadata = self.metadata_h.get_package_metadata(module_filepath = module_filepath)



    def prep_setup_dir(self,
                       metadata : dict = None,
                         requirements : str = None,
                         classifiers : list = None):

        if metadata is None:
            metadata = self.metadata

        if requirements is None:
            requirements = self.requirements

        if classifiers is None:
            classifiers = self.classifiers

        # create empty dir for setup
        self.setup_dir_h.flush_n_make_setup_dir()
        # copy module to dir
        self.setup_dir_h.copy_module_to_setup_dir()
        # create init file for new package
        self.setup_dir_h.create_init_file()
        # create setup.py
        self.setup_dir_h.write_setup_file(metadata = metadata,
                                          requirements = requirements,
                                          classifiers = classifiers)

    def make_package(self):

        # Define the command as a list of arguments
        command = ["python", "setup_dir/setup.py", "sdist", "bdist_wheel"]

        # Execute the command
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        return result


