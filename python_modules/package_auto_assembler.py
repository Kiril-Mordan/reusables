"""
Package auto assembler is a tool that meant to streamline creation of single module packages.
Its purpose is to automate as many aspects of python package creation as possible,
to shorten a development cycle of reusable components, maintain certain standard of quality
for reusable code. It provides tool to simplify the process of package creatrion
to a point that it can be triggered automatically within ci/cd pipelines,
with minimal preparations and requirements for new modules.
"""

# Imports
import logging
import os
import sys
import ast
import json
import csv
import codecs
from datetime import datetime
import re
import subprocess
import shutil
import pandas as pd #==2.1.1
import yaml
import nbformat
from nbconvert import MarkdownExporter
from nbconvert.preprocessors import ExecutePreprocessor
import attr #>=22.2.0
from stdlib_list import stdlib_list
import tempfile
import requests
import pip_audit #==2.7.3


# Metadata for package creation
__package_metadata__ = {
    "author": "Kyrylo Mordan",
    "author_email": "parachute.repo@gmail.com",
    "description": "A tool to automate package creation within ci based on just .py and optionally .ipynb file.",
    "keywords" : ['python', 'packaging']
}

@attr.s
class VersionHandler:

    versions_filepath = attr.ib()
    log_filepath = attr.ib()

    default_version = attr.ib(default="0.0.1")

    # output
    versions = attr.ib(init=False)

    logger = attr.ib(default=None)
    logger_name = attr.ib(default='Package Version Handler')
    loggerLvl = attr.ib(default=logging.INFO)
    logger_format = attr.ib(default=None)

    def __attrs_post_init__(self):
        self._initialize_logger()
        try:
            self.versions = self.get_versions()
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

        """
        Setup logging of package versions with datatime, package name and version in persistent csv file.
        """

        self.log_file = open(self.log_filepath, 'a', newline='', encoding="utf-8")
        self.csv_writer = csv.writer(self.log_file)
        # Write headers if the file is empty/new
        if os.stat(self.log_filepath).st_size == 0:
            self.csv_writer.writerow(['Timestamp', 'Package', 'Version'])


    def _create_versions(self):

        """
        Create empty file where versions will be stored.
        """

        self.logger.debug(f"Versions file was not found in location '{self.versions_filepath}', creating file!")
        with open(self.versions_filepath, 'w'):
            pass

    def _save_versions(self):

        """
        Persist versions in yaml file.
        """

        with open(self.versions_filepath, 'w') as file:
            yaml.safe_dump(self.versions, file)

    def _close_log_file(self):

        """
        Method for closing connection to log file, persists the changes in csv.
        """

        self.log_file.close()

    def __str__(self):

        """
        Method for diplaying the class.
        """

        return yaml.safe_dump(self.versions)

    def _parse_version(self, version):

        """
        Get components from the version string.
        """

        major, minor, patch = map(int, version.split('.'))
        return major, minor, patch

    def _format_version(self, major, minor, patch):

        """
        Form version string with components.
        """

        return f"{major}.{minor}.{patch}"

    def flush_versions(self):

        """
        Empty persist yaml, where versions were stored.
        """

        with open(self.versions_filepath, 'w', encoding='utf-8') as file:
            yaml.safe_dump({}, file)

    def flush_logs(self):

        """
        Empty persist csv, where version logs were stored.
        """

        # Close connection
        self._close_log_file()
        # Open the file in write mode to clear it, then write back only the headers
        with open(self.log_filepath, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Timestamp', 'Package', 'Version'])  # column headers
        # Reopen connection
        self._setup_logging()


    def log_version_update(self, package_name, new_version):

        """
        Update version logs when change in the versions occured.
        """

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.csv_writer.writerow([timestamp, package_name, new_version])
        self.log_file.flush()  # Ensure data is written to the file
        self._close_log_file()
        self._setup_logging()

    def get_logs(self,
                 log_filepath : str = None):

        """
        Return versions logs.
        """

        if log_filepath is None:
            log_filepath = self.log_filepath

        return pd.read_csv(log_filepath)

    def get_version(self, package_name : str = None):

        """
        Return specific version of the package.
        """

        return self.versions.get(package_name)


    def get_versions(self,
                     versions_filepath : str = None):

        """
        Return dictionary with all versions in the yaml file.
        """

        if versions_filepath is None:
            versions_filepath = self.versions_filepath

        # Open the YAML file
        with open(versions_filepath, 'r') as file:
            # Load the contents of the file
            return yaml.safe_load(file) or {}

    def update_version(self, package_name, new_version):

        """
        Update version of the named package with provided value and persist change.
        """

        self.versions[package_name] = new_version
        self._save_versions()
        self.log_version_update(package_name, new_version)

    def add_package(self,
                    package_name : str,
                    version : str = None):

        """
        Add new package with provided or default version.
        """

        if version is None:
            version = self.default_version

        if package_name not in self.versions:
            self.versions[package_name] = version
            self._save_versions()
            self.log_version_update(package_name, version)



    def increment_version(self,
                          package_name : str,
                          increment_type : str = None,
                          default_version : str = None):

        """
        Increment versions of the given package with 1 for a given increment type.
        """

        if default_version is None:
            default_version = self.default_version

        if increment_type is None:
            increment_type = 'patch'

        if package_name in self.versions:
            prev_version = self.versions[package_name]
            major, minor, patch = self._parse_version(prev_version)

            if increment_type == 'patch':
                patch += 1
            if increment_type == 'minor':
                minor += 1
            if increment_type == 'major':
                major += 1

            new_version = self._format_version(major, minor, patch)
            self.update_version(package_name, new_version)

            self.logger.debug(f"Incremented {increment_type} of {package_name} \
                from {prev_version} to {new_version}")
        else:
            self.logger.warning(f"There are no known versions of '{package_name}', {default_version} will be used!")
            self.update_version(package_name, default_version)



    def increment_major(self,
                        package_name : str,
                        default_version : str = None):

        """
        Increment major version of the given package with 1.
        """

        if default_version is None:
            default_version = self.default_version

        self.increment_version(package_name = package_name,
                             default_version = default_version,
                             increment_type = 'major')

    def increment_minor(self,
                        package_name : str,
                        default_version : str = None):

        """
        Increment minor version of the given package with 1.
        """

        if default_version is None:
            default_version = self.default_version

        self.increment_version(package_name = package_name,
                             default_version = default_version,
                             increment_type = 'minor')

    def increment_patch(self,
                        package_name : str,
                        default_version : str = None):

        """
        Increment patch version of the given package with 1.
        """

        if default_version is None:
            default_version = self.default_version

        self.increment_version(package_name = package_name,
                             default_version = default_version,
                             increment_type = 'patch')

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
class RequirementsHandler:

    module_filepath = attr.ib(default=None)

    package_mappings = attr.ib(default={}, type = dict)
    requirements_output_path  = attr.ib(default='./')
    output_requirements_prefix = attr.ib(default="requirements_")
    custom_modules_filepath = attr.ib(default=None)
    python_version = attr.ib(default='3.8')

    # output
    module_name = attr.ib(init=False)
    requirements_list = attr.ib(default=[], type = list)
    vulnerabilities = attr.ib(default=[], type = list)

    logger = attr.ib(default=None)
    logger_name = attr.ib(default='Package Requirements Handler')
    loggerLvl = attr.ib(default=logging.INFO)
    logger_format = attr.ib(default=None)

    def __attrs_post_init__(self):
        self._initialize_logger()
        self.vulnerabilities = []
        self.requirements_list = []


    def _initialize_logger(self):

        """
        Initialize a logger for the class instance based on the specified logging level and logger name.
        """

        if self.logger is None:
            logging.basicConfig(level=self.loggerLvl, format=self.logger_format)
            logger = logging.getLogger(self.logger_name)
            logger.setLevel(self.loggerLvl)

            self.logger = logger

    def check_vulnerabilities(self,
                              requirements_list : list = None,
                              raise_error : bool = True):

        """
        Checks vulnerabilities with pip-audit
        """

        if requirements_list is None:
            requirements_list = self.requirements_list

        # Create a temporary requirements file
        with tempfile.NamedTemporaryFile(delete=True, mode='w', suffix='.txt') as temp_req_file:
            for dep in requirements_list:
                temp_req_file.write(dep + '\n')
            temp_req_file.flush()

            # Run pip-audit on the temporary requirements file
            result = subprocess.run(
                ["pip-audit", "-r", temp_req_file.name, "--progress-spinner=off"],
                capture_output=True, text=True
            )

            print(result.stdout)
            self.logger.info(result.stderr)

            if result.returncode == 0:
                vulnerabilities = []
            else:

                if result.stdout:
                    # Access stdout
                    stdout = result.stdout.strip()

                    # Split into lines and skip the header (assumed to be the first two lines here)
                    lines = stdout.splitlines()
                    header_line = ['name', 'version', 'id', 'fix_versions']
                    data_lines = lines[2:]

                    # Prepare a list of dictionaries
                    vulnerabilities = []

                    # Process each data line into a dictionary
                    for line in data_lines:
                        values = line.split()

                        vd = {key:value for key,value in zip(header_line, values)}
                        if len(values) <= 3:
                            vd['fix_versions'] = None

                        vulnerabilities.append(vd)
                else:
                    vulnerabilities = []

        self.vulnerabilities += vulnerabilities

        if vulnerabilities and raise_error:
            raise ValueError("Found vulnerabilities, resolve them or ignore check to move forwards!")

    def list_custom_modules(self,
                            custom_modules_filepath : str = None):
        """
        List all custom module names in the specified directory.
        """

        if custom_modules_filepath is None:
            custom_modules_filepath = self.custom_modules_filepath

        if custom_modules_filepath is None:
            return []

        custom_modules = set()

        if custom_modules_filepath is None:
            self.logger.warning("No custom modules path was provided! Returning empty list!")
        else:
            for filename in os.listdir(custom_modules_filepath):
                if filename.endswith('.py') and not filename.startswith('__'):
                    module_name = filename.rsplit('.', 1)[0]
                    custom_modules.add(module_name)
        return list(custom_modules)

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
                               requirements_filepath : str) -> list:

        """
        Read requirements file and output a list.
        """


        with open(requirements_filepath, 'r') as file:
            requirements = [line.strip() for line in file if line.strip() and not line.startswith('#')]

        return requirements

    def extract_requirements(self,
                             module_filepath : str = None,
                             custom_modules : list = None,
                             package_mappings : dict = None,
                             python_version : str = None):

        """
        Extract requirements from the module.
        """

        if module_filepath is None:

            if self.module_filepath is None:
                raise ValueError("Parameter 'module_filepath' was not probided!")

            module_filepath = self.module_filepath

        if custom_modules is None:
            custom_modules = self.list_custom_modules()

        if package_mappings is None:
            package_mappings = self.package_mappings

        if python_version is None:
            python_version = self.python_version

        file_path = module_filepath
        module_name = os.path.basename(module_filepath)

        self.module_name = module_name

        # Separate regex patterns for 'import' and 'from ... import ...' statements
        import_pattern = re.compile(r"import (\S+)(?:\s+#(?:\s*(==|>=|<=|>|<)\s*([0-9.]+)))?")
        #from_import_pattern = re.compile(r"from (\S+) import [^#]+#\s*(==|>=|<=|>|<)\s*([0-9.]+)")

        from_import_pattern = re.compile(r"from (\S+) import [^#]+(?:#\s*(==|>=|<=|>|<)\s*([0-9.]+))?")


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

                # Skip local imports
                if module.startswith('.'):
                    continue

                # Extract the base package name
                module_root = module.split('.')[0]
                # Extracting package import leaf
                module_leaf = module.split('.')[-1]

                # Skip standard library and custom modules
                if self.is_standard_library(module_root, python_version) or module_root in custom_modules \
                    or self.is_standard_library(module_leaf, python_version) or module_leaf in custom_modules:
                    continue

                # Use the mapping to get the correct package name
                module = package_mappings.get(module_root, module_root)

                version_info = f"{version_constraint}{version}" if version_constraint and version else ""

                if version_info:
                    requirements.append(f"{module}{version_info}")
                else:
                    requirements.append(module)

                # deduplicate requirements
                requirements = [requirements[0]] + list(set(requirements[1:]))

        self.requirements_list += requirements

        return requirements

    def write_requirements_file(self,
                                module_name : str = None,
                                requirements : list = None,
                                output_path : str = None,
                                prefix : str = None):

        """
        Save extracted requirements.
        """

        if module_name is None:
            module_name = self.module_name

        if requirements is None:
            requirements = self.requirements_list

        if output_path is None:
            output_path = os.path.dirname(self.requirements_output_path)

        if prefix is None:
            prefix = self.output_requirements_prefix

        output_file = os.path.join(output_path, f"{prefix}{module_name}.txt")

        with open(output_file, 'w') as file:
            for req in requirements:
                file.write(req + '\n')

@attr.s
class MetadataHandler:


    module_filepath = attr.ib(default=None)

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


    def is_metadata_available(self, module_filepath : str = None):

        """
        Check is metadata is present in the module.
        """

        if module_filepath is None:
            module_filepath = self.module_filepath

        if module_filepath is None:
            self.logger.error("Provide module_filepath!")
            raise ValueError("module_filepath is None")

        try:
            with open(module_filepath, 'r') as file:
                for line in file:
                    # Check if the line defines __package_metadata__
                    if line.strip().startswith("__package_metadata__ ="):
                        return True
            return False
        except FileNotFoundError:
            return False

    def get_package_metadata(self, module_filepath : str = None):

        """
        Extract metadata from the given module if available.
        """

        if module_filepath is None:
            module_filepath = self.module_filepath

        if module_filepath is None:
            self.logger.error("Provide module_filepath!")
            raise ValueError("module_filepath is None")

        metadata_str = ""
        inside_metadata = False

        try:
            with open(module_filepath, 'r') as file:
                for line in file:
                    if '__package_metadata__ =' in line:
                        inside_metadata = True
                        metadata_str = line.split('#')[0]  # Ignore comments
                    elif inside_metadata:
                        metadata_str += line.split('#')[0]  # Ignore comments
                        if '}' in line:
                            break

            if metadata_str:
                try:
                    metadata = ast.literal_eval(metadata_str.split('=', 1)[1].strip())
                    return metadata
                except SyntaxError as e:
                    return f"Error parsing metadata: {e}"
            else:
                return "No metadata found in the file."

        except FileNotFoundError:
            return "File not found."
        except Exception as e:
            return f"An error occurred: {e}"

@attr.s
class LocalDependaciesHandler:

    main_module_filepath = attr.ib()
    dependencies_dir = attr.ib()
    save_filepath = attr.ib(default="./combined_module.py")
    add_empty_design_choices = attr.ib(default=False, type = bool)

    # output
    dependencies_names_list = attr.ib(init=False)
    combined_module = attr.ib(init=False)

    logger = attr.ib(default=None)
    logger_name = attr.ib(default='Local Dependacies Handler')
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

    def _read_module(self,
                    filepath : str) -> str:

        """
        Method for reading in module.
        """

        with open(filepath, 'r') as file:
            return file.read()

    def _extract_module_docstring(self,
                                 module_content : str) -> str:

        """
        Method for extracting title, module level docstring.
        """

        match = re.match(r'(""".*?"""|\'\'\'.*?\'\'\')', module_content, re.DOTALL)
        return match.group(0) if match else ''

    def _extract_imports(self,
                        module_content : str) -> str:

        """
        Method for extracting import statements from the module.
        """

        return re.findall(r'^(?:from\s+.+\s+)?import\s+.+$', module_content, re.MULTILINE)

    def _remove_module_docstring(self,
                                module_content : str) -> str:

        """
        Method for removing title, module level docstring.
        """

        return re.sub(r'^(""".*?"""|\'\'\'.*?\'\'\')', '', module_content, flags=re.DOTALL).strip()

    def _remove_imports(self,
                       module_content : str) -> str:

        """
        Method for removing import statements from the module.
        """

        module_content = re.sub(r'^(?:from\s+.+\s+)?import\s+.+$', '', module_content, flags=re.MULTILINE)
        return module_content.strip()

    def _remove_metadata(self, module_content: str) -> str:
        """
        Method for removing metadata from the module, including __package_metadata__ and __design_choices__.
        """

        lines = module_content.split('\n')
        new_lines = []
        inside_metadata = False

        for line in lines:
            if line.strip().startswith("__package_metadata__ = {") or line.strip().startswith("__design_choices__ = {"):
                inside_metadata = True
            elif inside_metadata and '}' in line:
                inside_metadata = False
                continue  # Skip adding this line to new_lines

            if not inside_metadata:
                new_lines.append(line)

        return '\n'.join(new_lines)

    def _extract_design_choices(self,
                                module_content: str,
                                module_name: str,
                                return_empty : bool = False) -> dict:

        """
        Extract __design_choices__ dictionary from the module.
        """

        design_choices_pattern = r'__design_choices__\s*=\s*({.*?})\s*(?:\n|$)'
        match = re.search(design_choices_pattern, module_content, re.DOTALL)
        if match:
            try:
                design_choices = eval(match.group(1))
                return {module_name: design_choices}
            except Exception as e:
                self.logger.error(f"Error evaluating __design_choices__ in {module_name}: {e}")
        if return_empty:
            return {module_name: {}}
        else:
            return None

    def _combine_design_choices(self, design_choices_list: list) -> dict:

        """
        Combine __design_choices__ dictionaries from all modules.
        """

        design_choices = {}
        for design_choice in design_choices_list:
            design_choices.update(design_choice)
        return design_choices


    def combine_modules(self,
                        main_module_filepath : str = None,
                        dependencies_dir : str = None,
                        add_empty_design_choices : bool = None) -> str:

        """
        Combining main module with its local dependancies.
        """

        if main_module_filepath is None:
            main_module_filepath = self.main_module_filepath

        if dependencies_dir is None:
            dependencies_dir = self.dependencies_dir

        if add_empty_design_choices is None:
            add_empty_design_choices = self.add_empty_design_choices


        # Read main module
        main_module_content = self._read_module(main_module_filepath)

        # Extract and preserve the main module's docstring and imports
        main_module_docstring = self._extract_module_docstring(main_module_content)
        main_module_imports = self._extract_imports(main_module_content)

        # List of dependency module names
        dependencies = [os.path.splitext(f)[0] for f in os.listdir(dependencies_dir) if f.endswith('.py')]
        self.dependencies_names_list = dependencies
        # Remove specific dependency imports from the main module
        for dep in dependencies:
            main_module_imports = [imp for imp in main_module_imports if f'{dep} import' not in imp]
        main_module_content = self._remove_imports(main_module_content)

        # Process dependency modules
        combined_content = ""
        design_choices_list = []
        for filename in dependencies:
            dep_content = self._read_module(os.path.join(dependencies_dir, f"{filename}.py"))
            # Extract design choices and add to list
            design_choices = self._extract_design_choices(dep_content, filename,add_empty_design_choices)
            if design_choices:
                design_choices_list.append(design_choices)

            dep_content = self._remove_module_docstring(dep_content)
            dep_content = self._remove_metadata(dep_content)
            dep_imports = self._extract_imports(dep_content)
            main_module_imports.extend(dep_imports)
            combined_content += self._remove_module_docstring(self._remove_imports(dep_content)) + "\n\n"

        # Combine design choices from all modules
        combined_design_choices = self._combine_design_choices(design_choices_list)
        combined_design_choices_str = f"__design_choices__ = {combined_design_choices}\n\n"

        # Combine everything
        unique_imports = sorted(set(main_module_imports), key=lambda x: main_module_imports.index(x))
        combined_module = main_module_docstring + "\n\n" + '\n'.join(unique_imports) + \
            "\n\n" + combined_design_choices_str + combined_content + main_module_content

        self.combined_module = combined_module

        return combined_module

    def save_combined_modules(self,
                              combined_module : str = None,
                              save_filepath : str = None):

        """
        Save combined module to .py file.
        """

        if combined_module is None:
            combined_module = self.combine_modules

        if save_filepath is None:
            save_filepath = self.save_filepath

        with open(save_filepath, 'w') as file:
            file.write(combined_module)


@attr.s
class LongDocHandler:

    notebook_path = attr.ib(default = None)
    markdown_filepath = attr.ib(default = None)
    timeout = attr.ib(default = 600, type = int)
    kernel_name = attr.ib(default = 'python', type = str)

    logger = attr.ib(default=None)
    logger_name = attr.ib(default='README Handler')
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

    def read_module_content(self,
                     filepath : str) -> str:

        """
        Method for reading in module.
        """

        with open(filepath, 'r') as file:
            return file.read()

    def extract_module_docstring(self,
                                 module_content : str) -> str:

        """
        Method for extracting title, module level docstring.
        """

        match = re.search(r'^("""(.*?)"""|\'\'\'(.*?)\'\'\')', module_content, flags=re.DOTALL)
        if match:
            docstring_content = match.group(2) if match.group(2) is not None else match.group(3)
            return docstring_content.strip()
        return None

    def _format_title(self, filename : str) -> str:
        """
        Formats the filename into a more readable title by removing the '.md' extension,
        replacing underscores with spaces, and capitalizing each word.
        """
        title_without_extension = os.path.splitext(filename)[0]  # Remove the .md extension
        title_with_spaces = title_without_extension.replace('_', ' ')  # Replace underscores with spaces
        # Capitalize the first letter of each word
        return ' '.join(word.capitalize() for word in title_with_spaces.split())

    def get_pypi_badge(self, module_name : str):

        """
        Get badge for module that was pushed to pypi.
        """

        # Convert underscores to hyphens
        module_name_hyphenated = module_name.replace('_', '-')
        pypi_module_link = f"https://pypi.org/project/{module_name_hyphenated}/"
        pypi_link = ""

        # Send a HEAD request to the PyPI module link
        response = requests.head(pypi_module_link)

        # Check if the response status code is 200 (OK)
        if response.status_code == 200:
            pypi_link = f"[![PyPiVersion](https://img.shields.io/pypi/v/{module_name_hyphenated})]({pypi_module_link})"

        return pypi_link


    def convert_notebook_to_md(self,
                               notebook_path : str = None,
                               output_path : str = None):

        """
        Convert example notebook to md without executing.
        """

        if notebook_path is None:
            notebook_path = self.notebook_path

        if output_path is None:
            output_path = self.markdown_filepath

        # Load the notebook
        with open(notebook_path, encoding='utf-8') as fh:
            notebook_node = nbformat.read(fh, as_version=4)

        # Create a Markdown exporter
        md_exporter = MarkdownExporter()

        # Process the notebook we loaded earlier
        (body, _) = md_exporter.from_notebook_node(notebook_node)

        # Write to the output markdown file
        with open(output_path, 'w', encoding='utf-8') as fh:
            fh.write(body)

        self.logger.debug(f"Converted {notebook_path} to {output_path}")

    def convert_and_execute_notebook_to_md(self,
                                           notebook_path : str = None,
                                           output_path : str = None,
                                           timeout : int = None,
                                           kernel_name: str = None):

        """
        Convert example notebook to md with executing.
        """

        if notebook_path is None:
            notebook_path = self.notebook_path

        if output_path is None:
            output_path = self.markdown_filepath

        if timeout is None:
            timeout = self.timeout

        if kernel_name is None:
            kernel_name = self.kernel_name

        # Load the notebook
        with open(notebook_path, encoding = 'utf-8') as fh:
            notebook_node = nbformat.read(fh, as_version=4)

        # Execute the notebook
        execute_preprocessor = ExecutePreprocessor(timeout=timeout, kernel_name=kernel_name)
        execute_preprocessor.preprocess(notebook_node, {'metadata': {'path': os.path.dirname(notebook_path)}})

        # Convert the notebook to Markdown
        md_exporter = MarkdownExporter()
        (body, _) = md_exporter.from_notebook_node(notebook_node)

        # Write to the output markdown file
        with open(output_path, 'w', encoding='utf-8') as fh:
            fh.write(body)

        self.logger.debug(f"Converted and executed {notebook_path} to {output_path}")

    def convert_dependacies_notebooks_to_md(self,
                                            dependacies_dir : str,
                                            dependacies_names : list,
                                            output_path : str = "../dep_md"):

        """
        Converts multiple dependacies into multiple md
        """

        for dep_name in dependacies_names:

            dependancy_path = os.path.join(dependacies_dir, dep_name + ".ipynb")

            self.convert_notebook_to_md(
                notebook_path = dependancy_path,
                output_path = os.path.join(output_path, f"{dep_name}.md")
            )

    def combine_md_files(self,
                         files_path : str,
                         md_files : list,
                         output_file : str,
                         content_section_title : str = "# Table of Contents\n"):
        """
        Combine all markdown (.md) files from the source directory into a single markdown file,
        and prepend a content section with a bullet point for each component.
        """
        # Ensure the source directory ends with a slash
        if not files_path.endswith('/'):
            files_path += '/'

        if md_files is None:
            # Get a list of all markdown files in the directory if not provided
            md_files = [f for f in os.listdir(files_path) if f.endswith('.md')]

        # Start with a content section
        content_section = content_section_title
        combined_content = ""

        for md_file in md_files:
            # Format the filename to a readable title for the content section
            title = self._format_title(md_file)
            # Add the title to the content section
            content_section += f"- {title}\n"

            with open(files_path + md_file, 'r', encoding='utf-8') as f:
                # Append each file's content to the combined_content string
                combined_content +=  f.read() + "\n\n"

        # Prepend the content section to the combined content
        final_content = content_section + "\n" + combined_content

        # Write the final combined content to the output file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(final_content)
        print(f"Combined Markdown with Table of Contents written to {output_file}")

    def return_long_description(self,
                                markdown_filepath : str = None):

        """
        Return long descrition for review as txt.
        """

        if markdown_filepath is None:
            markdown_filepath = self.markdown_filepath

        with codecs.open(markdown_filepath, encoding="utf-8") as fh:
            long_description = "\n" + fh.read()

        return long_description


@attr.s
class SetupDirHandler:

    module_filepath = attr.ib(type=str)
    module_name = attr.ib(default='', type=str)
    metadata = attr.ib(default={}, type=dict)
    requirements = attr.ib(default='', type=str)
    classifiers = attr.ib(default=[], type=list)
    setup_directory = attr.ib(default='./setup_dir')
    add_cli_tool = attr.ib(default=False, type = bool)

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

        """
        Remove everything from a given directory or create a new one if doesn't exists already.
        """

        if setup_directory is None:
            setup_directory = self.setup_directory

        # Flushing setup directory
        if os.path.exists(setup_directory):
            shutil.rmtree(setup_directory)
        os.makedirs(setup_directory)


    def copy_module_to_setup_dir(self,
                                 module_filepath : str = None,
                                 setup_directory : str = None):

        """
        Copy module to new setup directory.
        """


        if module_filepath is None:
            module_filepath = self.module_filepath

        if setup_directory is None:
            setup_directory = self.setup_directory

        # Copying module to setup directory
        shutil.copy(module_filepath, setup_directory)


    def create_init_file(self,
                         module_name : str = None,
                         setup_directory : str = None):

        """
        Create __init__.py for the package.
        """

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
                         module_docstring : str = None,
                         metadata : dict = None,
                         requirements : str = None,
                         classifiers : list = None,
                         setup_directory : str = None,
                         add_cli_tool : bool = None):

        """
        Create setup.py for the package.
        """

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

        if add_cli_tool is None:
            add_cli_tool = self.add_cli_tool

        metadata_str = ', '.join([f'{key}="{value}"' for key, value in metadata.items()])

        title = module_name.capitalize()
        title = title.replace("_"," ")

        long_description_intro = f"""# {title}\n\n"""

        if module_docstring:
            long_description_intro += f"""{module_docstring}\n\n"""

        if add_cli_tool:
            requirements += ['click']
            entry_points = {
                'console_scripts': [
                    f'{module_name} = {module_name}.cli:cli',
                ]
            }

        setup_content = f"""from setuptools import setup
import codecs
import os

here = os.path.abspath(os.path.dirname(__file__))
path_to_readme = os.path.join(here, "README.md")

"""

        setup_content += f'long_description = """{long_description_intro}"""'

        setup_content += f"""

if os.path.exists(path_to_readme):
  with codecs.open(path_to_readme, encoding="utf-8") as fh:
      long_description += fh.read()

setup(
    name="{module_name}",
    packages=["{module_name}"],
    install_requires={requirements},
    classifiers={classifiers},
    long_description=long_description,
    long_description_content_type='text/markdown',
"""

        if add_cli_tool:
            setup_content += f"""
    entry_points = {entry_points},
"""

        setup_content += f"""
    {metadata_str}
)
"""


        with open(os.path.join(setup_directory, 'setup.py'), 'w') as file:
            file.write(setup_content)

@attr.s
class ReleaseNotesHandler:

    # inputs
    filepath = attr.ib(default='release_notes.md', type=str)
    label_name = attr.ib(default=None, type=list)
    version = attr.ib(default='0.0.1', type=str)
    max_search_depth = attr.ib(default=2, type=int)

    # processed
    n_last_messages = attr.ib(default=1, type=int)
    existing_contents = attr.ib(default=None, type=list)
    commit_messages = attr.ib(default=None, type=list)
    filtered_messages = attr.ib(default=None, type=list)
    processed_messages = attr.ib(default=None, type=list)
    processed_note_entries  = attr.ib(default=None, type=list)


    logger = attr.ib(default=None)
    logger_name = attr.ib(default='Release Notes Handler')
    loggerLvl = attr.ib(default=logging.INFO)
    logger_format = attr.ib(default=None)

    def __attrs_post_init__(self):
        self._initialize_logger()

        if self.existing_contents is None:
            self.existing_contents = self.get_release_notes_content()
        if self.commit_messages is None:
            self._get_commits_since_last_merge()
        if self.filtered_messages is not []:
            self._filter_commit_messages_by_package()
        if self.processed_messages is None:
            self._clean_and_split_commit_messages()
        if self.processed_note_entries is None:
            self._create_release_note_entry()


    def _initialize_logger(self):

        """
        Initialize a logger for the class instance based on the specified logging level and logger name.
        """

        if self.logger is None:
            logging.basicConfig(level=self.loggerLvl, format=self.logger_format)
            logger = logging.getLogger(self.logger_name)
            logger.setLevel(self.loggerLvl)

            self.logger = logger

    def _deduplicate_with_exceptions(self,
                                     lst : list):

        seen = set()
        deduplicated = []
        version_headers = set()

        # Reverse iteration
        for item in reversed(lst):
            # If it's a version header, handle it differently
            if item.startswith("###"):
                if item not in version_headers:
                    version_headers.add(item)
                    if deduplicated and deduplicated[-1] != "\n":
                        deduplicated.append("\n")
                    deduplicated.append(item)
                    deduplicated.append("\n")  # Ensure newline after version header
            else:
                if item not in seen:
                    if item == "\n" and (not deduplicated or deduplicated[-1] == "\n"):
                        # Skip consecutive newlines
                        continue
                    seen.add(item)
                    deduplicated.append(item)
                    if item != "\n" and (deduplicated and deduplicated[-1] != "\n"):
                        deduplicated.append("\n")  # Ensure newline after each item

        # Reverse the result to restore original order
        deduplicated.reverse()

        # Clean up leading and trailing newlines
        while deduplicated and deduplicated[0] == "\n":
            deduplicated.pop(0)
        while deduplicated and deduplicated[-1] == "\n":
            deduplicated.pop()

        return deduplicated

    def _get_commits_since_last_merge(self, n_last_messages : int = 1):

        # First, find the last merge commit
        find_merge_command = ["git", "log", "--merges", "--format=%H", "-n", str(n_last_messages)]
        merge_result = subprocess.run(find_merge_command, capture_output=True, text=True)
        if merge_result.returncode != 0:
            raise Exception("Failed to find last merge commit")

        last_merge_commit_hash = merge_result.stdout.strip().split("\n")[n_last_messages-1]
        if not last_merge_commit_hash:
            raise Exception("No merge commits found")

        # Now, get all commits after the last merge commit
        log_command = ["git", "log", f"{last_merge_commit_hash}..HEAD", "--no-merges", "--format=%s"]
        log_result = subprocess.run(log_command, capture_output=True, text=True)
        if log_result.returncode != 0:
            raise Exception("Error running git log")

        # Each commit message is separated by newlines
        commit_messages = log_result.stdout.strip().split("\n")

        self.commit_messages = commit_messages

    def _filter_commit_messages_by_package(self,
                                           commit_messages : list = None,
                                           label_name : str = None):

        if commit_messages is None:
            commit_messages = self.commit_messages

        if label_name is None:
            label_name = self.label_name

        # This pattern will match messages that start with optional spaces, followed by [<package_name>],
        # possibly surrounded by spaces, and then any text. It is case-sensitive.
        pattern = re.compile(rf'\s*\[\s*{re.escape(label_name)}\s*\].*')

        # Filter messages that match the pattern
        filtered_messages = [msg for msg in commit_messages if pattern.search(msg)]

        if filtered_messages == []:
            self.n_last_messages += 1
            self.logger.warning(f"No relevant commit messages found!")
            if self.n_last_messages <= self.max_search_depth:
                self.logger.warning(f"..trying depth {self.n_last_messages} !")
                self._get_commits_since_last_merge(n_last_messages = self.n_last_messages)
                self._filter_commit_messages_by_package(
                    label_name = label_name)
                filtered_messages = self.filtered_messages

        self.filtered_messages = filtered_messages


    def _clean_and_split_commit_messages(self,
                                         commit_messages : list = None):

        if commit_messages is None:
            commit_messages = self.filtered_messages

        # Remove the package name tag and split messages by ";"
        cleaned_and_split_messages = []
        tag_pattern = re.compile(r'\[\s*[^]]*\]\s*')  # Matches the package name tag

        if len(commit_messages) == 0:
            self.logger.warning("No messages to clean were provided")
            cleaned_and_split_messages = []
        else:
            for msg in commit_messages:
                # Remove the package name tag from the message
                clean_msg = tag_pattern.sub('', msg).strip()
                # Split the message by ";"
                split_messages = clean_msg.split(';')
                # Strip whitespace from each split message and filter out any empty strings
                split_messages = [message.strip() for message in split_messages if message.strip()]
                cleaned_and_split_messages.extend(split_messages)

        self.processed_messages = cleaned_and_split_messages


    def _create_release_note_entry(self,
                                  existing_contents : str = None,
                                  version : str = None,
                                  new_messages : list = None):

        if existing_contents is None:
            if self.existing_contents is not None:
                existing_contents = self.existing_contents.copy()


        if version is None:
            version = self.version

        if new_messages is None:
            new_messages = self.processed_messages

        # Prepare the new release note section
        # new_release_note = f"### {version}\n\n"
        # for msg in new_messages:
        #     new_release_note += f"    - {msg}\n"

        if new_messages:
            new_release_notes = [f"### {version}\n"] + ["\n"]
            for msg in new_messages:
                new_release_notes += [f"    - {msg}\n"]
        else:
            new_release_notes = []

        # If there are existing contents, integrate the new entry
        if existing_contents:
            # Find the location of the first version heading to insert the new release note right after
            index = 0
            for line in existing_contents:
                if line.strip().startswith('###'):
                    break
                index += 1

            # Insert the new release note section into the contents
            for new_release_note in new_release_notes:
                existing_contents.insert(index, new_release_note)
                index += 1
        else:

            # If no existing contents, start a new list of contents
            existing_contents = ["# Release notes\n"] + ["\n"]
            for new_release_note in new_release_notes:
                existing_contents += new_release_note

        existing_contents = self._deduplicate_with_exceptions(
            lst=existing_contents)

        self.processed_note_entries = existing_contents


    def get_release_notes_content(self,
                                  filepath : str = None) -> str:

        """
        Get release notes content.
        """

        if filepath is None:
            filepath = self.filepath

        if os.path.exists(filepath):
            # Read the existing release notes
            with open(filepath, 'r') as file:
                content = file.readlines()
        else:
            # No existing file, start with empty contents
            content = None

        return content

    def save_release_notes(self,
                           filepath : str = None,
                           note_entries : str = None):

        """
        Save updated release notes content.
        """

        if filepath is None:
            filepath = self.filepath

        if note_entries is None:
            note_entries = self.processed_note_entries

        if self.processed_messages != []:
            # Write the updated or new contents back to the file
            with open(filepath, 'w') as file:
                file.writelines(note_entries)


@attr.s
class MkDocsHandler:

    # inputs
    package_name = attr.ib(type=str)
    docs_file_paths = attr.ib(type=list)

    module_docstring = attr.ib(default=None, type=str)
    pypi_badge = attr.ib(default='', type=str)
    license_badge = attr.ib(default='', type=str)

    project_name = attr.ib(default="temp_project", type=str)

    # processed
    logger = attr.ib(default=None)
    logger_name = attr.ib(default='MkDocs Handler')
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

    def create_mkdocs_project(self, project_name: str = None):
        """
        Create a new MkDocs project.
        """

        if project_name is None:
            project_name = self.project_name

        subprocess.run(["mkdocs", "new", project_name])
        print(f"Created new MkDocs project: {project_name}")

    def create_mkdocs_dir(self, project_name: str = None):
        """
        Create a new dir for MkDocs project.
        """

        if project_name is None:
            project_name = self.project_name

        if os.path.exists(project_name):
            shutil.rmtree(project_name)
        os.makedirs(project_name)

        print(f"Created new MkDocs dir: {project_name}")

    def move_files_to_docs(self, file_paths: dict = None, project_name: str = None):
        """
        Move files from given list of paths to the docs directory.
        """

        if file_paths is None:
            file_paths = self.docs_file_paths

        if project_name is None:
            project_name = self.project_name

        docs_dir = os.path.join(project_name, "docs")
        if not os.path.exists(docs_dir):
            os.makedirs(docs_dir)

        for file_path in file_paths:
            if os.path.exists(file_path):
                filename = file_paths[file_path]
                destination = os.path.join(docs_dir, filename)

                # Ensure unique filenames
                if os.path.exists(destination):
                    base, extension = os.path.splitext(filename)
                    counter = 1
                    while os.path.exists(destination):
                        new_filename = f"{base}_{counter}{extension}"
                        destination = os.path.join(docs_dir, new_filename)
                        counter += 1

                shutil.copy(file_path, destination)
                print(f"Copied {file_path} to {destination}")
            else:
                print(f"File not found: {file_path}")

    def _clean_filename(self, filename: str, package_name: str) -> str:
        """
        Remove the package name prefix from the filename.

        Args:
            filename (str): The original filename.
            package_name (str): The package name to remove.

        Returns:
            str: The cleaned filename without the package name prefix.
        """
        if filename.startswith(f"{package_name}-"):
          return filename[len(package_name)+1:]
        # if filename == f"{package_name}.md":
        #   return "usage-examples.md"

        return filename

    def create_index(self,
                     project_name: str = None,
                     module_docstring : str = None,
                     pypi_badge : str = None,
                     license_badge : str = None):

        """
        Create index page with small intro.
        """

        if project_name is None:
            project_name = self.package_name

        if module_docstring is None:
            module_docstring = self.module_docstring

        if pypi_badge is None:
            pypi_badge = self.pypi_badge

        if license_badge is None:
            license_badge = self.license_badge

        package_name = project_name.replace("_","-")

        content = f"""# Intro

{pypi_badge} {license_badge}

{module_docstring}

## Installation

```bash
pip install {package_name}
```
        """

        mkdocs_index_path = os.path.join("temp_project","docs", "index.md")
        with open(mkdocs_index_path, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"index.md has been created with site_name: {package_name}")



    def generate_markdown_for_images(self, package_name: str = None, project_name: str = None):
        """
        Generate .md files for each .png file in the specified directory based on naming rules.

        Args:
            directory (str): Path to the directory containing .png files.
            package_name (str): The package name to use for naming conventions.
        """

        if package_name is None:
            package_name = self.package_name

        if project_name is None:
            project_name = self.project_name

        directory = os.path.join(project_name, "docs")

        if not os.path.exists(directory):
            print(f"The directory {directory} does not exist.")
            return

        for filename in os.listdir(directory):
            if filename.endswith('.png'):
                cleaned_name = self._clean_filename(filename, package_name)
                md_filename = f"{os.path.splitext(cleaned_name)[0]}.md"

                md_filepath = os.path.join(directory, md_filename)

                # Write Markdown content
                with open(md_filepath, 'w') as md_file:
                    md_content = f"![{filename}](./{filename})"
                    md_file.write(md_content)
                print(f"Created {md_filepath}")

    def create_mkdocs_yml(self, package_name: str = None, project_name: str = None):
        """
        Create mkdocs.yml with a given site_name.
        """

        if project_name is None:
            project_name = self.project_name

        if package_name is None:
            package_name = self.package_name

        package_name = package_name.capitalize()
        package_name = package_name.replace("_"," ")

        content = f"""site_name: {package_name}

theme:
  name: material
  palette:
    # Palette toggle for light mode
    - scheme: default
      primary: green
      accent: green
      toggle:
        icon: material/lightbulb
        name: Switch to dark mode

    # Palette toggle for dark mode
    - scheme: slate
      primary: green
      accent: green
      toggle:
        icon: material/lightbulb-outline
        name: Switch to light mode

extra_css:
  - css/extra.css
        """

        mkdocs_yml_path = os.path.join(project_name, "mkdocs.yml")
        with open(mkdocs_yml_path, "w") as file:
            file.write(content.strip())
        print(f"mkdocs.yml has been created with site_name: {package_name}")

        css_dir = os.path.join(project_name, "docs", "css")
        if not os.path.exists(css_dir):
            os.makedirs(css_dir)

        css_content = """
/* Ensure tables are scrollable horizontally */
table {
  display: block;
  width: 100%;
  overflow-x: auto;
  white-space: nowrap;
}

/* Ensure tables and their parent divs don't overflow the content area */
.dataframe {
  display: block;
  width: 100%;
  overflow-x: auto;
  white-space: nowrap;
}

.dataframe thead th {
  text-align: right;
}

.dataframe tbody tr th {
  vertical-align: top;
}

.dataframe tbody tr th:only-of-type {
  vertical-align: middle;
}

/* Ensure the whole content area is scrollable */
.md-content__inner {
  overflow-x: auto;
  padding: 20px; /* Add some padding for better readability */
}

/* Fix layout issues caused by the theme */
.md-main__inner {
  max-width: none;
}
        """

        css_path = os.path.join(css_dir, "extra.css")
        with open(css_path, "w") as file:
            file.write(css_content.strip())
        print(f"Custom CSS created at {css_path}")

    def build_mkdocs_site(self, project_name: str = None):
        """
        Serve the MkDocs site.
        """

        if project_name is None:
            project_name = self.project_name

        os.chdir(project_name)
        subprocess.run(["mkdocs", "build"])
        os.chdir("..")

    def serve_mkdocs_site(self, project_name: str = None):
        """
        Serve the MkDocs site.
        """

        if project_name is None:
            project_name = self.project_name

        try:
            os.chdir(project_name)
            subprocess.run(["mkdocs", "serve"])
        except Exception as e:
            print(e)
        finally:
            os.chdir("..")

@attr.s
class CliHandler:

    # inputs
    cli_module_filepath = attr.ib()
    setup_directory = attr.ib()

    # processed
    logger = attr.ib(default=None)
    logger_name = attr.ib(default='MkDocs Handler')
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

    def prepare_script(self,
                       cli_module_filepath: str = None,
                       setup_directory : str = None):

        """
        Prepare cli script for packaging.
        """

        if cli_module_filepath is None:
            cli_module_filepath = self.cli_module_filepath

        if setup_directory is None:
            setup_directory = self.setup_directory

        # Copying module to setup directory
        shutil.copy(cli_module_filepath, os.path.join(setup_directory, "cli.py"))

        return True

@attr.s
class PackageAutoAssembler:
    # pylint: disable=too-many-instance-attributes

    ## inputs
    module_name = attr.ib(type=str)

    ## paths
    module_filepath = attr.ib(type=str)
    cli_module_filepath = attr.ib(default=None)
    mapping_filepath = attr.ib(default=None)
    dependencies_dir = attr.ib(default=None)
    example_notebook_path = attr.ib(default=None)
    versions_filepath = attr.ib(default='./lsts_package_versions.yml')
    log_filepath = attr.ib(default='./version_logs.csv')
    setup_directory = attr.ib(default='./setup_dir')

    # optional parameters
    classifiers = attr.ib(default=['Development Status :: 3 - Alpha',
                                    'Intended Audience :: Developers',
                                    'Intended Audience :: Science/Research',
                                    'Programming Language :: Python :: 3',
                                    'Programming Language :: Python :: 3.9',
                                    'Programming Language :: Python :: 3.10',
                                    'Programming Language :: Python :: 3.11',
                                    'License :: OSI Approved :: MIT License',
                                    'Topic :: Scientific/Engineering'])
    requirements_list = attr.ib(default=[])
    execute_readme_notebook = attr.ib(default=True, type = bool)
    python_version = attr.ib(default="3.8")
    version_increment_type = attr.ib(default="patch", type = str)
    default_version = attr.ib(default="0.0.1", type = str)
    kernel_name = attr.ib(default = 'python', type = str)
    check_vulnerabilities = attr.ib(default=True, type = bool)

    ## handler classes
    setup_dir_h_class = attr.ib(default=SetupDirHandler)
    version_h_class = attr.ib(default=VersionHandler)
    import_mapping_h_class = attr.ib(default=ImportMappingHandler)
    local_dependacies_h_class = attr.ib(default=LocalDependaciesHandler)
    requirements_h_class = attr.ib(default=RequirementsHandler)
    metadata_h_class = attr.ib(default=MetadataHandler)
    long_doc_h_class = attr.ib(default=LongDocHandler)
    cli_h_class = attr.ib(default=CliHandler)

    ## handlers
    setup_dir_h = attr.ib(default = None, type = SetupDirHandler)
    version_h = attr.ib(default = None, type = VersionHandler)
    import_mapping_h = attr.ib(default = None, type=ImportMappingHandler)
    local_dependacies_h = attr.ib(default = None, type=LocalDependaciesHandler)
    requirements_h = attr.ib(default = None, type=RequirementsHandler)
    metadata_h = attr.ib(default = None, type=MetadataHandler)
    long_doc_h = attr.ib(default = None, type=LongDocHandler)
    cli_h = attr.ib(default = None, type=CliHandler)

    ## output
    add_cli_tool = attr.ib(default = None, type = bool)
    package_result = attr.ib(init=False)
    metadata = attr.ib(init=False)

    logger = attr.ib(default=None)
    logger_name = attr.ib(default='Package Auto Assembler')
    loggerLvl = attr.ib(default=logging.INFO)
    logger_format = attr.ib(default=None)

    def __attrs_post_init__(self):
        self._initialize_logger()
        self._initialize_metadata_handler()
        self._initialize_import_mapping_handler()


    def _initialize_logger(self):

        """
        Initialize a logger for the class instance based on the specified logging level and logger name.
        """

        if self.logger is None:
            logging.basicConfig(level=self.loggerLvl, format=self.logger_format)
            logger = logging.getLogger(self.logger_name)
            logger.setLevel(self.loggerLvl)

            self.logger = logger

    def _initialize_metadata_handler(self):

        """
        Initialize metadata handler with available parameters.
        """

        self.metadata_h = self.metadata_h_class(
            module_filepath = self.module_filepath)

    def _initialize_version_handler(self):

        """
        Initialize version handler with available parameters.
        """

        self.version_h = self.version_h_class(
            versions_filepath = self.versions_filepath,
            log_filepath = self.log_filepath,
            default_version = self.default_version)

    def _initialize_requirements_handler(self):

        """
        Initialize requirements handler with available parameters.
        """

        self.requirements_h = self.requirements_h_class(
            module_filepath = self.module_filepath,
            custom_modules_filepath = self.dependencies_dir,
            python_version = self.python_version)

    def _initialize_import_mapping_handler(self):

        """
        Initialize import mapping handler with available parameters.
        """

        self.import_mapping_h = self.import_mapping_h_class(
            mapping_filepath = self.mapping_filepath)

    def _initialize_local_dependacies_handler(self):

        """
        Initialize local dependanies handler with available parameters.
        """

        self.local_dependacies_h = self.local_dependacies_h_class(
            main_module_filepath = self.module_filepath,
            dependencies_dir = self.dependencies_dir)

    def _initialize_long_doc_handler(self):

        """
        Initialize long doc handler with available parameters.
        """

        self.long_doc_h = self.long_doc_h_class(
            notebook_path = self.example_notebook_path,
            kernel_name = self.kernel_name)

    def _initialize_setup_dir_handler(self):

        """
        Initialize setup dir handler with available parameters.
        """

        self.setup_dir_h = self.setup_dir_h_class(
            module_name = self.module_name,
            module_filepath = self.module_filepath,
            setup_directory = self.setup_directory,
            logger = self.logger)

    def _initialize_cli_handler(self):

        """
        Initialize cli handler with available parameters.
        """

        self.cli_h = self.cli_h_class(
            cli_module_filepath = self.cli_module_filepath,
            setup_directory = self.setup_directory,
            logger = self.logger)

    def add_metadata_from_module(self, module_filepath : str = None):

        """
        Add metadata extracted from the module.
        """

        if self.metadata_h is None:
            self._initialize_metadata_handler()

        if module_filepath is None:
            module_filepath = self.module_filepath

        # extracting package metadata
        self.metadata = self.metadata_h.get_package_metadata(module_filepath = module_filepath)


    def add_or_update_version(self,
                              module_name : str = None,
                              version_increment_type : str = None,
                              version : str = None,
                              versions_filepath : str = None,
                              log_filepath : str = None):

        """
        Increment version and creates entry in version logs.
        """

        if self.version_h is None:
            self._initialize_version_handler()

        if module_name is None:
            module_name = self.module_name

        if version_increment_type is None:
            version_increment_type = self.version_increment_type

        if version is None:
            version = self.default_version

        if versions_filepath is None:
            versions_filepath = self.versions_filepath

        if log_filepath is None:
            log_filepath = self.log_filepath

        self.version_h.increment_version(package_name = module_name,
                                         increment_type = version_increment_type,
                                         default_version = version)

        self.metadata['version'] = self.version_h.get_version(package_name=module_name)

    def prep_setup_dir(self):

        """
        Prepare setup directory.
        """

        if self.setup_dir_h is None:
            self._initialize_setup_dir_handler()

        # create empty dir for setup
        self.setup_dir_h.flush_n_make_setup_dir()
        # copy module to dir
        self.setup_dir_h.copy_module_to_setup_dir()
        # create init file for new package
        self.setup_dir_h.create_init_file()


    def merge_local_dependacies(self,
                                main_module_filepath : str = None,
                                dependencies_dir : str = None,
                                save_filepath : str = None):

        """
        Combine local dependacies and main module into one file.
        """

        if self.local_dependacies_h is None:
            self._initialize_local_dependacies_handler()

        if main_module_filepath is None:
            main_module_filepath = self.module_filepath

        if dependencies_dir is None:
            dependencies_dir = self.dependencies_dir

        if save_filepath is None:
            save_filepath = os.path.join(self.setup_directory, os.path.basename(main_module_filepath))

        # combime module with its dependacies
        self.local_dependacies_h.save_combined_modules(
            combined_module=self.local_dependacies_h.combine_modules(main_module_filepath = main_module_filepath,
                                                                     dependencies_dir = dependencies_dir),
            save_filepath=save_filepath
        )

        # switch filepath for the combined one
        self.module_filepath = save_filepath

    def add_requirements_from_module(self,
                                     module_filepath : str = None,
                                     import_mappings : str = None,
                                     check_vulnerabilities : bool = None):

        """
        Extract and add requirements from the module.
        """

        if self.requirements_h is None:
            self._initialize_requirements_handler()

        if module_filepath is None:
            module_filepath = self.module_filepath

        if check_vulnerabilities is None:
            check_vulnerabilities = self.check_vulnerabilities

        if import_mappings is None:

            if self.mapping_filepath is None:
                import_mappings = {}
            else:
                import_mappings = self.import_mapping_h.load_package_mappings()

        custom_modules = self.requirements_h.list_custom_modules()

        # extracting package requirements
        self.requirements_list = self.requirements_list + \
            self.requirements_h.extract_requirements(
                package_mappings=import_mappings,
                module_filepath=module_filepath,
                custom_modules=custom_modules)
        if check_vulnerabilities:
            self.requirements_h.check_vulnerabilities()

    def add_readme(self,
                    example_notebook_path : str = None,
                    output_path : str = None,
                    execute_notebook : bool = None):

        """
        Make README file based on usage example.
        """

        if self.long_doc_h is None:
            self._initialize_long_doc_handler()

        if example_notebook_path is None:
            example_notebook_path = self.example_notebook_path

        if output_path is None:
            output_path = os.path.join(self.setup_directory,
                                       "README.md")

        if execute_notebook is None:
            execute_notebook = self.execute_readme_notebook

        if execute_notebook:
            # converting example notebook to md
            self.long_doc_h.convert_and_execute_notebook_to_md(
                notebook_path = example_notebook_path,
                output_path = output_path
            )
        else:
            self.long_doc_h.convert_notebook_to_md(
                notebook_path = example_notebook_path,
                output_path = output_path
            )


    def prep_setup_file(self,
                       module_name : str = None,
                       cli_module_filepath : str = None,
                       metadata : dict = None,
                       requirements : str = None,
                       classifiers : list = None,
                       module_filepath : str = None,
                       module_docstring : str = None):

        """
        Assemble setup.py file.
        """

        if self.setup_dir_h is None:
            self._initialize_setup_dir_handler()

        if cli_module_filepath is None:
            cli_module_filepath = self.cli_module_filepath

        if metadata is None:
            metadata = self.metadata

        if requirements is None:
            requirements = self.requirements_list

        if classifiers is None:
            classifiers = self.classifiers

        if module_filepath is None:
            module_filepath = self.module_filepath

        if module_name is None:
            module_name = self.module_name

        if module_docstring is None:

            if self.long_doc_h is None:
                self._initialize_long_doc_handler()

            module_content = self.long_doc_h.read_module_content(filepath = module_filepath)

            module_docstring = self.long_doc_h.extract_module_docstring(module_content = module_content)


        if cli_module_filepath is not None \
            and os.path.exists(cli_module_filepath) \
                and os.path.isfile(cli_module_filepath):

            if self.cli_h is None:
                self._initialize_cli_handler()

            add_cli_tool = self.cli_h.prepare_script(
                cli_module_filepath = cli_module_filepath
            )
        else:
            add_cli_tool = None

        # create setup.py
        self.setup_dir_h.write_setup_file(module_name = module_name,
                                          module_docstring = module_docstring,
                                          metadata = metadata,
                                          requirements = requirements,
                                          classifiers = classifiers,
                                          add_cli_tool = add_cli_tool)

    def make_package(self,
                     setup_directory : str = None):

        """
        Create a package.
        """

        if setup_directory is None:
            setup_directory = self.setup_directory

        # Define the command as a list of arguments
        command = ["python", os.path.join(setup_directory, "setup.py"), "sdist", "bdist_wheel"]

        # Execute the command
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        return result

    def test_install_package(self,
                             module_name : str = None,
                             remove_temp_files : bool = True):

        """
        Test install package to environment and optional remove temp files.
        """

        if module_name is None:
            module_name = self.module_name

        # Reinstall the module from the wheel file
        wheel_files = [f for f in os.listdir('dist') if f.endswith('-py3-none-any.whl')]
        for wheel_file in wheel_files:
            subprocess.run([sys.executable, "-m", "pip", "install", "--force-reinstall",
                            os.path.join('dist', wheel_file)], check=True)

        if remove_temp_files:
            # Clean up the build directories and other generated files
            shutil.rmtree('build', ignore_errors=True)
            shutil.rmtree('dist', ignore_errors=True)
            shutil.rmtree(module_name, ignore_errors=True)
            shutil.rmtree(f"{module_name}.egg-info", ignore_errors=True)
