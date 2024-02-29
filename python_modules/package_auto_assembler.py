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
import logging
import os
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
    requirements_list = attr.ib(init=False)

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

        self.requirements_list = requirements

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

    def _format_title(self, filename : str) -> str:
        """
        Formats the filename into a more readable title by removing the '.md' extension,
        replacing underscores with spaces, and capitalizing each word.
        """
        title_without_extension = os.path.splitext(filename)[0]  # Remove the .md extension
        title_with_spaces = title_without_extension.replace('_', ' ')  # Replace underscores with spaces
        # Capitalize the first letter of each word
        return ' '.join(word.capitalize() for word in title_with_spaces.split())


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
                         metadata : dict = None,
                         requirements : str = None,
                         classifiers : list = None,
                         setup_directory : str = None):

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

        metadata_str = ', '.join([f'{key}="{value}"' for key, value in metadata.items()])
        setup_content = f"""from setuptools import setup
import codecs
import os

here = os.path.abspath(os.path.dirname(__file__))
path_to_readme = os.path.join(here, "README.md")

if os.path.exists(path_to_readme):
  with codecs.open(path_to_readme, encoding="utf-8") as fh:
      long_description = fh.read()
else:
  long_description = ''

setup(
    name="{module_name}",
    packages=["{module_name}"],
    install_requires={requirements},
    classifiers={classifiers},
    long_description=long_description,
    long_description_content_type='text/markdown',
    {metadata_str}
)
        """
        with open(os.path.join(setup_directory, 'setup.py'), 'w') as file:
            file.write(setup_content)



@attr.s
class PackageAutoAssembler:
    # pylint: disable=too-many-instance-attributes

    ## inputs
    module_name = attr.ib(type=str)

    ## paths
    module_filepath = attr.ib(type=str)
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

    ## handlers
    setup_dir_h = attr.ib(default=SetupDirHandler)
    version_h = attr.ib(default=VersionHandler)
    import_mapping_h = attr.ib(default=ImportMappingHandler)
    local_dependacies_h = attr.ib(default=LocalDependaciesHandler)
    requirements_h = attr.ib(default=RequirementsHandler)
    metadata_h = attr.ib(default=MetadataHandler)
    long_doc_h = attr.ib(default=LongDocHandler)

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

        self.metadata_h = self.metadata_h(module_filepath = self.module_filepath)

        self.version_h = self.version_h(versions_filepath = self.versions_filepath,
                                        log_filepath = self.log_filepath,
                                        default_version = self.default_version)

        self.import_mapping_h = self.import_mapping_h(mapping_filepath = self.mapping_filepath)

        self.local_dependacies_h = self.local_dependacies_h(main_module_filepath = self.module_filepath,
                                                            dependencies_dir = self.dependencies_dir)

        self.requirements_h = self.requirements_h(module_filepath = self.module_filepath,
                                                  custom_modules_filepath = self.dependencies_dir,
                                                  python_version = self.python_version)

        self.long_doc_h = self.long_doc_h(notebook_path = self.example_notebook_path,
                                          kernel_name = self.kernel_name)

        self.setup_dir_h = self.setup_dir_h(module_name = self.module_name,
                                            module_filepath = self.module_filepath,
                                            setup_directory = self.setup_directory,
                                            logger = self.logger)



    def add_metadata_from_module(self, module_filepath : str = None):

        """
        Add metadata extracted from the module.
        """

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
                                     import_mappings : str = None):

        """
        Extract and add requirements from the module.
        """

        if module_filepath is None:
            module_filepath = self.module_filepath

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

    def add_readme(self,
                    example_notebook_path : str = None,
                    output_path : str = None,
                    execute_notebook : bool = None):

        """
        Make README file based on usage example.
        """

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
                       metadata : dict = None,
                       requirements : str = None,
                       classifiers : list = None):

        """
        Assemble setup.py file.
        """

        if metadata is None:
            metadata = self.metadata

        if requirements is None:
            requirements = self.requirements_list

        if classifiers is None:
            classifiers = self.classifiers

        # create setup.py
        self.setup_dir_h.write_setup_file(metadata = metadata,
                                          requirements = requirements,
                                          classifiers = classifiers)

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
