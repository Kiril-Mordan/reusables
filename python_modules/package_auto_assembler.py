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
import numpy #==1.26.0
import nbformat
from nbconvert import MarkdownExporter #==7.16.4
from nbconvert.preprocessors import ExecutePreprocessor
import attr #>=22.2.0
from stdlib_list import stdlib_list
import tempfile
import requests
import pip_audit #==2.7.3
import mkdocs #==1.6.0
import difflib
import importlib
import importlib.metadata
from packaging import version
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import importlib.resources as pkg_resources


# Metadata for package creation
__package_metadata__ = {
    "author": "Kyrylo Mordan",
    "author_email": "parachute.repo@gmail.com",
    "description": "A tool to automate package creation within ci based on just .py and optionally .ipynb file.",
    "keywords" : ['python', 'packaging'],
    'license' : 'mit'
}

@attr.s
class VersionHandler:

    versions_filepath = attr.ib()
    log_filepath = attr.ib()

    default_version = attr.ib(default="0.0.1")

    read_files = attr.ib(default=True)

    # output
    versions = attr.ib(init=False)

    logger = attr.ib(default=None)
    logger_name = attr.ib(default='Package Version Handler')
    loggerLvl = attr.ib(default=logging.INFO)
    logger_format = attr.ib(default=None)

    def __attrs_post_init__(self):
        self._initialize_logger()
        if self.read_files:
            try:
                self.versions = self.get_versions()
            except Exception as e:
                self._create_versions()
                self.versions = {}
            self._setup_logging()
        else:
            self.versions = {}


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


    def log_version_update(self, 
                            package_name : str, 
                            new_version : str):

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

    def update_version(self, 
                       package_name : str, 
                       new_version : str,
                       save : bool = True):

        """
        Update version of the named package with provided value and persist change.
        """

        self.versions[package_name] = new_version
        if save:
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

    def get_latest_pip_version(self, package_name : str):

        """
        Extracts latest version of the packages wit pip if possible.
        """

        package_name = package_name.replace('_', '-')

        try:

            command = ["pip", "index", "versions", package_name]
            
            result = subprocess.run(command, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"Error fetching package versions: {result.stderr.strip()}")

            output = result.stdout.strip()

            # Extract versions using regex
            version_pattern = re.compile(r'Available versions: (.+)')
            match = version_pattern.search(output)

            if match:
                versions = match.group(1).split(", ")
                latest_version = versions[0]
                return latest_version
            else:
                raise Exception("No versions found for the package.")

        except Exception as e:
            self.logger.error("Failed to extract latest version with pip!")
            self.logger.warning("Using latest version from provided file instead!")
            return None

    def increment_version(self,
                          package_name : str,
                          version : str = None,
                          increment_type : str = None,
                          default_version : str = None,
                          save : bool = True,
                          usepip : bool = True):

        """
        Increment versions of the given package with 1 for a given increment type.
        """

        if default_version is None:
            default_version = self.default_version

        if increment_type is None:
            increment_type = 'patch'

        prev_version = None
        if usepip:
            prev_version = self.get_latest_pip_version(
                package_name = package_name
            )

        if prev_version is None:
            prev_version = self.versions.get(package_name, self.default_version)

        if version is None:
            major, minor, patch = self._parse_version(prev_version)

            if increment_type == 'patch':
                patch += 1
            if increment_type == 'minor':
                patch = 0
                minor += 1
            if increment_type == 'major':
                patch = 0
                minor = 0
                major += 1
            version = self._format_version(major, minor, patch)

        new_version = version
        self.update_version(package_name, new_version, save)

        self.logger.debug(f"Incremented {increment_type} of {package_name} \
            from {prev_version} to {new_version}")
        # else:

        #     if usepip:
        #         prev_version = self.get_latest_pip_version(
        #             package_name = package_name
        #         )
        #     if prev_version is None:
        #         self.logger.warning(f"There are no known versions of '{package_name}', {default_version} will be used!")
        #     else:
        #         default_version = prev_version
        #     self.update_version(package_name, default_version, save)



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

    mapping_filepath = attr.ib(default = None)
    base_mapping_filepath = attr.ib(default = None)

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
                              mapping_filepath : str = None,
                              base_mapping_filepath : str = None):
        """
        Get file with mappings for packages which import names differ from install names.
        """

        if mapping_filepath is None:
            mapping_filepath = self.mapping_filepath

        if base_mapping_filepath is None:
            base_mapping_filepath = self.base_mapping_filepath

        
        if base_mapping_filepath is None:
            with pkg_resources.path('package_auto_assembler.artifacts', 
            'package_mapping.json') as path:
                base_mapping_filepath = path

        if (mapping_filepath is not None) \
            and os.path.exists(mapping_filepath):

            with open(mapping_filepath, 'r') as file:
                mapping_file = json.load(file)
        else:
            mapping_file = {}

        if os.path.exists(base_mapping_filepath):

            with open(base_mapping_filepath, 'r') as file:
                base_mapping_file = json.load(file)
        else:
            base_mapping_file = {}

        base_mapping_file.update(mapping_file)

        return base_mapping_file


@attr.s
class RequirementsHandler:

    module_filepath = attr.ib(default=None)

    package_mappings = attr.ib(default={}, type = dict)
    requirements_output_path  = attr.ib(default='./')
    output_requirements_prefix = attr.ib(default="requirements_")
    custom_modules_filepath = attr.ib(default=None)
    add_header = attr.ib(default=True, type = bool)
    python_version = attr.ib(default='3.8')

    # output
    module_name = attr.ib(init=False)
    requirements_list = attr.ib(default=[], type = list)
    optional_requirements_list = attr.ib(default=[], type = list)
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

    def _keep_most_constrained(self, requirements : list):

        try:
            # Regex to capture the package name, extras, version operator, and version
            pattern = re.compile(r"(\S+?)(?:\[(\w+)\])?(?:(==|>=|<=|>|<)\s*([\d\.]+))?$")
            
            # Dictionary to hold the most constrained version for each package
            package_constraints = {}

            for req in requirements:
                match = pattern.match(req)
                if match:
                    pkg_name, extra, operator, ver = match.groups()
                    
                    # Create a tuple representing the constraint: (extras, operator, version)
                    constraint = (extra, operator, ver)
                    
                    # If the package is not already in the dictionary, or if the new requirement has more constraints
                    if pkg_name not in package_constraints:
                        package_constraints[pkg_name] = (req, constraint)
                    else:
                        # Extract the current best requirement
                        current_req, current_constraint = package_constraints[pkg_name]
                        
                        # Compare the number of constraints
                        new_constraints_count = sum(x is not None for x in constraint)
                        current_constraints_count = sum(x is not None for x in current_constraint)
                        
                        if new_constraints_count > current_constraints_count:
                            package_constraints[pkg_name] = (req, constraint)
                        elif new_constraints_count == current_constraints_count:
                            # If they have the same number of constraints, compare versions
                            if ver and current_constraint[2]:
                                if version.parse(ver) > version.parse(current_constraint[2]):
                                    package_constraints[pkg_name] = (req, constraint)

            # Return the most constrained requirements
            return [req for req, _ in package_constraints.values()]
        except Exception as e:
            return requirements

    def check_vulnerabilities(self,
                              requirements_list : list = None,
                              raise_error : bool = True):

        """
        Checks vulnerabilities with pip-audit
        """

        if requirements_list is None:
            requirements_list = self.requirements_list + self.optional_requirements_list


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
                             python_version : str = None,
                             add_header : bool = None):

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

        if add_header is None:
            add_header = self.add_header

        file_path = module_filepath
        module_name = os.path.basename(module_filepath)

        self.module_name = module_name

        # Matches 'import module as alias' with optional version comment
        #import_pattern_as = re.compile(r"import (\S+)(?: as (\S+))?(?:\s+#(?:\s*(==|>=|<=|>|<)\s*([0-9.]+)))?")
        import_pattern_as = re.compile(
            r"import (\S+)(?: as (\S+))?(?:\s+#(?:\[(\w+)\])?(?:\s*(==|>=|<=|>|<)\s*([0-9.]+))?)?")

        # Separate regex patterns for 'import' and 'from ... import ...' statements
        import_pattern = re.compile(
            r"import (\S+)(?:\s+#(?:\[(\w+)\])?(?:\s*(==|>=|<=|>|<)\s*([0-9.]+))?)?")
        
        #from_import_pattern = re.compile(r"from (\S+) import [^#]+#\s*(==|>=|<=|>|<)\s*([0-9.]+)")
        from_import_pattern = re.compile(
            r"from (\S+) import ([\w\s,]+)(?:\s*#(?:\[(\w+)\])?\s*(==|>=|<=|>|<)\s*([0-9.]+))?"
        )

        # optional requirements
        optional_import_pattern_as = re.compile(
            r"#! import (\S+)(?: as (\S+))?(?:\s+#(?:\[(\w+)\])?(?:\s*(==|>=|<=|>|<)\s*([0-9.]+))?)?")
        optional_import_pattern = re.compile(
            r"#!\s*import\s+(\S+)(?:\s+#(?:\[(\w+)\])?(?:\s*(==|>=|<=|>|<)\s*([\d\.]+))?)?"
        )
        optional_from_import_pattern = re.compile(
            r"#!\s*from\s+(\S+)\s+import\s+([\w\s,]+)(?:\s*#(?:\s*\[(\w+)\])?(?:\s*(==|>=|<=|>|<)\s*([0-9.]+))?)?"
        )


        requirements = []
        optional_requirements = []
        if add_header:
            new_header = [f'### {module_name}']
        else:
            new_header = []

        with open(file_path, 'r') as file:
            for line in file:
                import_match = import_pattern.match(line)
                from_import_match = from_import_pattern.match(line)
                import_as_match = import_pattern_as.match(line)

                optional_import_match = optional_import_pattern.match(line)
                optional_from_import_match = optional_from_import_pattern.match(line)
                optional_import_as_match = optional_import_pattern_as.match(line)

                module = None
                optional_module = None

                if import_as_match:
                    module, alias, extra_require, version_constraint, version = import_as_match.groups()
                elif from_import_match:
                    module, _, extra_require, version_constraint, version = from_import_match.groups()
                elif import_match:
                    module, extra_require, version_constraint, version = import_match.groups()
                elif optional_import_match:
                    optional_module, optional_extra_require, optional_version_constraint, optional_version = optional_import_match.groups()
                elif optional_from_import_match:
                    optional_module, _, optional_extra_require, optional_version_constraint, optional_version = optional_from_import_match.groups()
                elif optional_import_as_match:
                    optional_module, optional_alias, optional_extra_require, optional_version_constraint, optional_version = optional_import_as_match.groups()
                else:
                    continue

                skip = False
                    
                if module:

                    # Skip local imports
                    if module.startswith('.'):
                        skip = True

                    if not skip:

                        # Extract the base package name
                        module_root = module.split('.')[0]
                        # Extracting package import leaf
                        module_leaf = module.split('.')[-1]

                    # Skip standard library and custom modules
                    if self.is_standard_library(module_root, python_version) or module_root in custom_modules \
                        or self.is_standard_library(module_leaf, python_version) or module_leaf in custom_modules:
                        skip = True

                    if not skip:

                        # Use the mapping to get the correct package name
                        module = package_mappings.get(module_root, module_root)

                        extra_require_ad = f"[{extra_require}]" if extra_require else ""
                        version_info = f"{version_constraint}{version}" if version_constraint and version else ""

                        if version_info:
                            requirements.append(f"{module}{extra_require_ad}{version_info}")
                        else:
                            requirements.append(f"{module}{extra_require_ad}")

                        # deduplicate requirements
                        requirements = [requirements[0]] + list(set(requirements[1:]))

                skip = False

                if optional_module:

                    # Skip local imports
                    if optional_module.startswith('.'):
                        skip = True

                    if not skip:

                        # Extract the base package name
                        module_root = optional_module.split('.')[0]
                        # Extracting package import leaf
                        module_leaf = optional_module.split('.')[-1]

                    # Skip standard library and custom modules
                    if self.is_standard_library(module_root, python_version) or module_root in custom_modules \
                        or self.is_standard_library(module_leaf, python_version) or module_leaf in custom_modules:
                        skip = True

                    if not skip:

                        # Use the mapping to get the correct package name
                        optional_module = package_mappings.get(module_root, module_root)

                        optional_extra_require_ad = f"[{optional_extra_require}]" if optional_extra_require else ""
                        optional_version_info = f"{optional_version_constraint}{optional_version}" \
                            if optional_version_constraint and optional_version else ""

                        if optional_version_info:
                            optional_requirements.append(f"{optional_module}{optional_extra_require_ad}{optional_version_info}")
                        else:
                            optional_requirements.append(f"{optional_module}{optional_extra_require_ad}")

        if self.requirements_list:
            header = [self.requirements_list.pop(0)]
        else:
            header = []

        requirements_list = header + new_header + list(set(self.requirements_list + requirements))
        optional_requirements_list = list(set(self.optional_requirements_list + optional_requirements))

        requirements_list = self._keep_most_constrained(requirements_list)
        optional_requirements_list = self._keep_most_constrained(optional_requirements_list)

        self.requirements_list = requirements_list
        self.optional_requirements_list = optional_requirements_list

        return requirements_list, optional_requirements_list

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
    header_name = attr.ib(default="__package_metadata__")

    metadata_status = attr.ib(default={})

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


    def is_metadata_available(self,
                              module_filepath : str = None,
                              header_name : str = None):

        """
        Check is metadata is present in the module.
        """

        if module_filepath is None:
            module_filepath = self.module_filepath

        if header_name is None:
            header_name = self.header_name

        if module_filepath is None:
            self.logger.error("Provide module_filepath!")
            raise ValueError("module_filepath is None")

        try:
            with open(module_filepath, 'r') as file:
                for line in file:
                    # Check if the line defines __package_metadata__
                    if line.strip().startswith(f"{header_name} ="):
                        self.metadata_status[header_name] = True
                        return True
            self.metadata_status[header_name] = False
            return False
        except FileNotFoundError:
            self.metadata_status[header_name] = False
            return False

    def get_package_metadata(self,
                             module_filepath : str = None,
                             header_name : str = None):

        """
        Extract metadata from the given module if available.
        """

        if module_filepath is None:
            module_filepath = self.module_filepath

        if header_name is None:
            header_name = self.header_name

        if module_filepath is None:
            self.logger.error("Provide module_filepath!")
            raise ValueError("module_filepath is None")

        metadata_str = ""
        inside_metadata = False
        expecting_closing_brackes = 0

        try:
            with open(module_filepath, 'r') as file:
                for line in file:

                    if '{' in line:
                        expecting_closing_brackes += 1
                    if '}' in line:
                        expecting_closing_brackes -= 1

                    if f'{header_name} =' in line:
                        inside_metadata = True
                        metadata_str = line.split('#')[0]  # Ignore comments
                    elif inside_metadata:
                        metadata_str += line.split('#')[0]  # Ignore comments
                        if ('}' in line) and (expecting_closing_brackes <= 0):
                            break

            if metadata_str:
                try:
                    metadata = ast.literal_eval(metadata_str.split('=', 1)[1].strip())
                    if 'keywords' not in metadata.keys():
                        metadata['keywords'] = []
                    metadata['keywords'].append('aa-paa-tool')
                    return metadata
                except SyntaxError as e:
                    return f"Error parsing metadata: {e}"
            else:

                if self.metadata_status.get(header_name, False):
                    return {}

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
        main_module_content = self._remove_module_docstring(main_module_content)
        main_module_imports = self._extract_imports(main_module_content)

        # List of dependency module names
        dependencies = [os.path.splitext(f)[0] for f in os.listdir(dependencies_dir) if f.endswith('.py')]
        # List of dependency bundles
        dependencies_folders = [os.path.splitext(f)[0] for f in os.listdir(dependencies_dir) if os.path.isdir(os.path.join(dependencies_dir,f))]
        # List of dependencies from bundles
        bundle_dependencies = [os.path.splitext(f)[0] for bundle in dependencies_folders for f in os.listdir(os.path.join(dependencies_dir, bundle)) if f.endswith('.py')]
        bundle_dep_path = [os.path.join(bundle, f) for bundle in dependencies_folders for f in os.listdir(os.path.join(dependencies_dir, bundle)) if f.endswith('.py')]
        
        self.dependencies_names_list = dependencies + bundle_dependencies
        # Filtering relevant dependencies
        module_local_deps = [dep for dep in dependencies for module in main_module_imports if f'{dep} import' in module]
        module_bundle_deps = [dep for dep in bundle_dependencies for module in main_module_imports if f'{dep} import' in module]


        # Remove specific dependency imports from the main module
        for dep in module_local_deps:
            main_module_imports = [imp for imp in main_module_imports if f'{dep} import' not in imp]

        for dep in module_bundle_deps:
            main_module_imports = [imp for imp in main_module_imports if f'{dep} import' not in imp]

        main_module_content = self._remove_imports(main_module_content)

        # Process dependency modules
        combined_content = ""
        design_choices_list = []
        for filename in module_local_deps:

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

        # Process bundle dependency modules
        for file_path, filename in zip(bundle_dep_path, bundle_dependencies):

            if filename in module_bundle_deps:

                dep_content = self._read_module(os.path.join(dependencies_dir, file_path))
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

        if os.path.exists(notebook_path):

            # Load the notebook
            with open(notebook_path, encoding='utf-8') as fh:
                notebook_node = nbformat.read(fh, as_version=4)

            # Create a Markdown exporter
            md_exporter = MarkdownExporter()

            # Process the notebook we loaded earlier
            (body, _) = md_exporter.from_notebook_node(notebook_node)

            self.logger.debug(f"Converted {notebook_path} to {output_path}")

        else:
            body = ""

        # Write to the output markdown file
        with open(output_path, 'w', encoding='utf-8') as fh:
            fh.write(body)

            

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

        if os.path.exists(notebook_path):

            # Load the notebook
            with open(notebook_path, encoding = 'utf-8') as fh:
                notebook_node = nbformat.read(fh, as_version=4)

            # Execute the notebook
            execute_preprocessor = ExecutePreprocessor(timeout=timeout, kernel_name=kernel_name)
            execute_preprocessor.preprocess(notebook_node, {'metadata': {'path': os.path.dirname(notebook_path)}})

            # Convert the notebook to Markdown
            md_exporter = MarkdownExporter()
            (body, _) = md_exporter.from_notebook_node(notebook_node)

            self.logger.debug(f"Converted and executed {notebook_path} to {output_path}")

        else:

            body = ""

            # Write to the output markdown file
            with open(output_path, 'w', encoding='utf-8') as fh:
                fh.write(body)

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
    docstring = attr.ib(default=None, type=str)
    license_path = attr.ib(default=None, type=str)
    license_label = attr.ib(default=None, type=str)
    docs_url = attr.ib(default=None, type=str)
    metadata = attr.ib(default={}, type=dict)
    cli_metadata = attr.ib(default={}, type=dict)
    requirements = attr.ib(default=[], type=list)
    optional_requirements = attr.ib(default=None, type=list)
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

    def copy_license_to_setup_dir(self,
                                 license_path : str = None,
                                 setup_directory : str = None):

        """
        Copy module to new setup directory.
        """


        if license_path is None:
            license_path = self.license_path

        if setup_directory is None:
            setup_directory = self.setup_directory
        
        if license_path:
            # Copying module to setup directory
            shutil.copy(license_path, setup_directory)


    def create_init_file(self,
                         module_name : str = None,
                         docstring : str = None,
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
        
        if docstring is None:
            docstring = self.docstring

        init_content = ''
        if docstring:
            init_content = f"""\n\"\"\"\n{docstring}\n\"\"\"\n"""
        init_content += f"""from .{module_name} import *\n"""

        # Creating temporary __init__.py file
        init_file_path = os.path.join(setup_directory, '__init__.py')
        with open(init_file_path, 'w') as init_file:
            init_file.write(init_content)

    def write_setup_file(self,
                         module_name : str = None,
                         module_docstring : str = None,
                         metadata : dict = None,
                         license_label : str = None,
                         docs_url : str = None,
                         cli_metadata : dict = None,
                         requirements : list = None,
                         optional_requirements : list = None,
                         classifiers : list = None,
                         setup_directory : str = None,
                         add_cli_tool : bool = None,
                         add_artifacts : bool = None,
                         artifacts_filepaths : dict = None):

        """
        Create setup.py for the package.
        """


        import pkg_resources

        if module_name is None:
            if self.module_name == '':
                module_name = os.path.basename(self.module_filepath)
            else:
                module_name = self.module_name

        if metadata is None:
            metadata = self.metadata

        if metadata is None:
            metadata = {}

        if cli_metadata is None:
            cli_metadata = self.cli_metadata

        if requirements is None:
            requirements = self.requirements

        if requirements is None:
            requirements = []
        else:
            requirements = [req for req in requirements if not req.startswith("###")]

        if optional_requirements is None:
            optional_requirements = self.optional_requirements

        if classifiers is None:
            classifiers = self.classifiers

        if license_label is None:
            license_label = self.license_label

        if docs_url is None:
            docs_url = self.docs_url

        if add_cli_tool is None:
            add_cli_tool = self.add_cli_tool

        if add_artifacts is None:
            add_artifacts = self.add_artifacts

        paa_version = pkg_resources.get_distribution("package_auto_assembler").version
        
        if classifiers is None:
            classfiers = []
            #classifiers = [f"PAA-Version :: {paa_version}"]
        # else:
        #     classifiers.append(f"PAA-Version :: {paa_version}")

        #classifiers.append(f"PAA-CLI :: {add_cli_tool}")

        if 'classifiers' in metadata.keys():
            classifiers+=metadata['classifiers']
            del metadata['classifiers']

        if setup_directory is None:
            setup_directory = self.setup_directory

        extras_require = None

        if optional_requirements:

            extras_require = {req.split("=")[0].split("<")[0] : [req] for req in optional_requirements}
            extras_require['all'] = optional_requirements

        if 'extras_require' in metadata.keys():

            if extras_require is None:
                extras_require = {}

            extras_require.update(metadata['extras_require'])
            del metadata['extras_require']

        if 'install_requires' in metadata.keys():
            requirements+=metadata['install_requires']
            del metadata['install_requires']

        metadata_str = None
        metadata_str = ',\n    '.join([f'{key}="{value}"' for key, value in metadata.items()])


        title = module_name.capitalize()
        title = title.replace("_"," ")

        long_description_intro = f"""# {title}\n\n"""

        if module_docstring:
            long_description_intro += f"""{module_docstring}\n\n"""

    
        if add_cli_tool:
            entry_points = {
                'console_scripts': [
                    f'{module_name} = {module_name}.cli:cli',
                ]
            }

            if "name" in cli_metadata.keys():
                entry_points = {
                'console_scripts': [
                    f"{cli_metadata['name']} = {module_name}.cli:cli",
                ]
            }

        setup_content = "from setuptools import setup\n\n"

        setup_content += "import codecs\n"
        setup_content += "import os\n\n"
        setup_content += "here = os.path.abspath(os.path.dirname(__file__))\n"
        setup_content += 'path_to_readme = os.path.join(here, "README.md")\n\n'

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
        if metadata_str:
            setup_content += f"""    {metadata_str},"""

        if add_cli_tool:
            setup_content += f"""
    entry_points = {entry_points},
"""
        if extras_require:
            setup_content += f"""
    extras_require = {extras_require},
"""
        if license_label and ('license' not in metadata.keys()):
            setup_content += f"""
    license = "{license_label}",
"""

        if docs_url and ('url' not in metadata.keys()):
            setup_content += f"""    url = {docs_url},
"""

        if add_artifacts and artifacts_filepaths != {}:
            setup_content += f"""    include_package_data = True,
"""

            package_data = {
                f"{module_name}" : [art for art in artifacts_filepaths],
            }
            setup_content += f"""    package_data = {package_data} ,
"""

        setup_content += f"""    )
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
    version_update_label = attr.ib(default=None, type=str)


    logger = attr.ib(default=None)
    logger_name = attr.ib(default='Release Notes Handler')
    loggerLvl = attr.ib(default=logging.INFO)
    logger_format = attr.ib(default=None)

    def __attrs_post_init__(self):
        self._initialize_logger()

        if self.filepath:

            self._initialize_notes()

            if self.existing_contents is None:
                self.existing_contents = self.get_release_notes_content()

        if self.commit_messages is None:
            self._get_commits_since_last_merge()
        if self.filtered_messages is not []:
            self._filter_commit_messages_by_package()
        if self.processed_messages is None:
            self._clean_and_split_commit_messages()
        # if self.processed_note_entries is None:
        #     self._create_release_note_entry()


    def _initialize_logger(self):

        """
        Initialize a logger for the class instance based on the specified logging level and logger name.
        """

        if self.logger is None:
            logging.basicConfig(level=self.loggerLvl, format=self.logger_format)
            logger = logging.getLogger(self.logger_name)
            logger.setLevel(self.loggerLvl)

            self.logger = logger

    def _initialize_notes(self):

        if not os.path.exists(self.filepath):
            self.logger.warning(f"No release notes were found in {self.filepath}, new will be initialized!")

            content = """# Release notes\n"""
            with open(self.filepath, 'w', encoding='utf-8') as file:
                file.write(content)

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
            #raise Exception("Failed to find last merge commit")
            self.logger.warning("Failed to find last merge commit")
            self.commit_messages = []
            return True

        merge_result_p = merge_result.stdout.strip().split("\n")

        if len(merge_result_p) > (n_last_messages-1):
            last_merge_commit_hash = merge_result_p[n_last_messages-1]
        else:
            last_merge_commit_hash = None
        if not last_merge_commit_hash:
            self.logger.warning("No merge commits found")
            self.commit_messages = []
            return True

        # Now, get all commits after the last merge commit
        log_command = ["git", "log", f"{last_merge_commit_hash}..HEAD", "--no-merges", "--format=%s"]
        log_result = subprocess.run(log_command, capture_output=True, text=True)
        if log_result.returncode != 0:
            #raise Exception("Error running git log")
            self.logger.warning("Error running git log")
            self.commit_messages = []
            return True

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

    # Function to convert version string to a tuple of integers
    def _version_key(self, version : str):
        return tuple(map(int, version.split('.')))

    def extract_version_update(self, commit_messages : list = None):

        """
        Extract the second set of brackets and recognize version update.
        """

        if commit_messages is None:
            commit_messages = self.filtered_messages

        versions = []
        major = None
        minor = None
        patch = None

        for commit_message in commit_messages:
            match = re.search(r'\[([^\]]+)]\[([^\]]+)]', commit_message)
            if match:
                second_bracket_content = match.group(2)
                if re.match(r'^\d+\.\d+\.\d+$', second_bracket_content):
                    version = second_bracket_content
                    versions.append(version)
                elif second_bracket_content in ['+','+.','+..']:
                    major = 'major'
                elif second_bracket_content in ['.+','.+.']:
                    minor = 'minor'
                elif second_bracket_content in ['..+']:
                    patch = 'patch'

        # Return the highest priority match
        if versions:
            # Sort the list using the custom key function
            version = sorted(versions, key=self._version_key)[-1]

            self.version = version
            return version
        elif major:
            self.version_update_label = major
            return major
        elif minor:
            self.version_update_label = minor
            return minor
        elif patch:
            self.version_update_label = patch
            return patch
        else:
            self.version_update_label = 'patch'
            return patch

    def extract_latest_version(self, release_notes : list = None):

        """
        Extracts latest version from provided release notes.
        """

        if release_notes is None:
            release_notes = self.existing_contents

        latest_version = None
        
        for line in release_notes:
            line = line.strip()
            if line.startswith("###"):
                # Extract the version number after ###
                version = line.split("###")[-1].strip()
                # Update the latest version to the first version found
                if latest_version is None or version > latest_version:
                    latest_version = version

        return latest_version

    def create_release_note_entry(self,
                                  existing_contents : str = None,
                                  version : str = None,
                                  new_messages : list = None):

        if self.processed_note_entries is not None:
            self.logger.warning("Processed note entries already exist and will be overwritten!")

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

    def move_files_to_docs(self, 
                           file_paths: dict = None, 
                           project_name: str = None,
                           package_name: str = None):
        """
        Move files from given list of paths to the docs directory.
        """

        if file_paths is None:
            file_paths = self.docs_file_paths

        if project_name is None:
            project_name = self.project_name

        if package_name is None:
            package_name = self.package_name

        docs_dir = os.path.join(project_name, "docs")
        if not os.path.exists(docs_dir):
            os.makedirs(docs_dir)

        for file_path in file_paths:
            if os.path.exists(file_path):
                filename = file_paths[file_path]
                cleaned_filename = self._clean_filename(
                            filename, package_name)
                destination = os.path.join(docs_dir, cleaned_filename)

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

        return filename

    def create_index(self,
                     package_name: str = None,
                     project_name: str = None,
                     module_docstring : str = None,
                     pypi_badge : str = None,
                     license_badge : str = None):

        """
        Create index page with small intro.
        """

        if project_name is None:
            project_name = self.project_name

        if module_docstring is None:
            module_docstring = self.module_docstring

        if module_docstring is None:
            module_docstring = ''

        if pypi_badge is None:
            pypi_badge = self.pypi_badge

        if pypi_badge is None:
            pypi_badge = ''

        if license_badge is None:
            license_badge = self.license_badge

        if license_badge is None:
             license_badge = ''

        if package_name is None:
            package_name = self.package_name

        content = f"""# Intro

{pypi_badge} {license_badge}

{module_docstring}

"""


        if pypi_badge != '':
            content += f"""
## Installation

```bash
pip install {package_name.replace("_", "-")}
```

"""

        mkdocs_index_path = os.path.join(project_name,"docs", "index.md")
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
    logger_name = attr.ib(default='Cli Handler')
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
class ArtifactsHandler:

    # inputs
    setup_directory = attr.ib(default = None)
    module_name = attr.ib(default = None)
    artifacts_filepaths = attr.ib(default = None)
    artifacts_dir = attr.ib(default = None)
    manifest_lines = attr.ib(default = [])

    # processed
    logger = attr.ib(default=None)
    logger_name = attr.ib(default='Artifacts Handler')
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

    def load_additional_artifacts(self, artifacts_dir : str = None):

        """
        Load artifacts filepath from provided folder.
        """

        if artifacts_dir is None:
            artifacts_dir = self.artifacts_dir

        if artifacts_dir:

            if os.path.exists(artifacts_dir):
                artifacts_filepaths = {
                    path : os.path.join(artifacts_dir, path) \
                        for path in os.listdir(artifacts_dir)
                }

        return artifacts_filepaths



    def get_packaged_artifacts(self, 
                              module_name : str = None):

        """
        Get names and paths to package artifacts
        """

        if module_name is None:
            module_name = self.module_name

        with pkg_resources.path(module_name, 'artifacts') as path:
            package_path = path

        if os.path.exists(package_path):
            package_files = os.listdir(package_path)

            package_artifacts = {file_name : os.path.join(package_path, file_name) \
                for file_name in package_files}
        else:
            package_artifacts = {}
        
        return package_artifacts


    def make_manifest(self,
                    module_name : str = None,
                    artifacts_filepaths: dict = None,
                    setup_directory : str = None):

        """
        Prepare cli script for packaging.
        """

        if module_name is None:
            module_name = self.module_name

        if artifacts_filepaths is None:
            artifacts_filepaths = self.artifacts_filepaths

        if setup_directory is None:
            setup_directory = self.setup_directory

        # create folder for paa files
        os.makedirs(os.path.join(setup_directory,'.paa.tracking'))

        try:
            # Get the package version
            version = importlib.metadata.version('package-auto-assembler')
            
            # Write the version to a text file
            with open(os.path.join(setup_directory,'.paa.tracking','.paa.version'), 
            'w') as file:
                file.write(f"{version}")
        except Exception as e:
            self.logger.warning(e)

        # create folder for optional artifacts
        if artifacts_filepaths != {}:
            os.makedirs(os.path.join(setup_directory,'artifacts'))

        manifest_lines = []
        updated_artifacts_filepaths = {}
        # copy files and create manifest
        for artifact_name, artifacts_filepath in artifacts_filepaths.items():

            # artifact_name = os.path.basename(
            #     os.path.normpath(artifacts_filepath))
            
            if os.path.isdir(artifacts_filepath):
                shutil.copytree(artifacts_filepath, 
                    os.path.join(setup_directory, artifact_name))
                artifact_name += "/**/*"
                manifest_lines.append(
                    f"recursive-include {module_name}/{artifact_name} \n")
            else:
                shutil.copy(artifacts_filepath, 
                    os.path.join(setup_directory, artifact_name))
                manifest_lines.append(f"include {module_name}/{artifact_name} \n")

            updated_artifacts_filepaths[artifact_name] = artifacts_filepath
            
        manifest_lines.append(f"include {module_name}/{'.paa.tracking/.paa.version'} \n")
        updated_artifacts_filepaths['.paa.tracking/.paa.version'] = os.path.join(setup_directory,'.paa.tracking','.paa.version')
        
        self.artifacts_filepaths = updated_artifacts_filepaths
        self.manifest_lines = manifest_lines


    def write_mafifest(self):

        manifest_filepath = os.path.join(self.setup_directory,
                'MANIFEST.in')

        if os.path.exists(manifest_filepath):
            with open(manifest_filepath, 'r') as file:
                manifest_lines = file.readlines()
        else:
            manifest_lines = []


        manifest_lines += self.manifest_lines

        # write/update manifest
        if manifest_lines:
            with open(manifest_filepath, 
            'w') as file:
                file.writelines(manifest_lines)

        return True

@attr.s
class FastApiHandler:

    # inputs
    fastapi_routes_filepath = attr.ib(default = None)
    setup_directory = attr.ib(default = None)

    docs_prefix = attr.ib(default = "/mkdocs")

    # processed
    logger = attr.ib(default=None)
    logger_name = attr.ib(default='FastAPI Handler')
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

    def _include_docs(self,
                      app,
                      docs_paths,
                      docs_prefix = None):

        if docs_prefix is None:
            docs_prefix = self.docs_prefix

        i_str = ''
        i = 0
        for docs_path in docs_paths:
            app.mount(f"{docs_prefix}{i_str}", 
                      StaticFiles(directory=docs_path, 
                                  html=True))
            i += 1
            i_str = str(i)


        return app

    def _include_package_routes(self, 
                                app, 
                                package_names : list, 
                                routes_paths : list):
    
        
        for package_name in package_names:
            try:

                package_name = package_name.replace('-','_')

                # Import the package
                package = importlib.import_module(package_name)
                
                # Get the package's directory
                package_dir = os.path.dirname(package.__file__)
                
                # Construct the path to routes.py
                routes_file_path = os.path.join(package_dir, 'routes.py')

                # Construct the path to site
                docs_file_path = os.path.join(package_dir,'mkdocs', 'site')

                if os.path.exists(routes_file_path):
                    routes_module = importlib.import_module(f"{package_name}.routes")
                    app.include_router(routes_module.router)
                
                if os.path.exists(docs_file_path):
                    app = self._include_docs(
                        app = app,
                        docs_paths = [docs_file_path],
                        docs_prefix = f"/{package_name.replace('_','-')}/docs"
                    )

            except ImportError as e:
                print(e)
                print(f"Error importing routes from {package_name}: {e}")
                sys.exit(1)

        for routes_path in routes_paths:
            try:
                # Generate a module name from the file path
                module_name = routes_path.rstrip('.py').replace('/', '.').replace('\\', '.')
                
                # Load the module from the specified file path
                spec = importlib.util.spec_from_file_location(module_name, routes_path)
                if spec is None:
                    print(f"Could not load spec from {routes_path}")
                    sys.exit(1)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Check if the module has a 'router' attribute
                if hasattr(module, 'router'):
                    app.include_router(module.router)
                else:
                    print(f"The module at {routes_path} does not have a 'router' attribute.")
                    sys.exit(1)
            except FileNotFoundError:
                print(f"File not found: {routes_path}")
                sys.exit(1)
            except Exception as e:
                print(f"Error loading routes from {routes_path}: {e}")
                sys.exit(1)

        return app

    def prepare_routes(self,
                       fastapi_routes_filepath: str = None,
                       setup_directory : str = None):

        """
        Prepare fastapi routes for packaging.
        """

        if fastapi_routes_filepath is None:
            fastapi_routes_filepath = self.fastapi_routes_filepath

        if setup_directory is None:
            setup_directory = self.setup_directory

        if fastapi_routes_filepath is None:
            raise ImportError("Parameter fastapi_routes_filepath is missing!")

        if setup_directory is None:
            raise ImportError("Parameter setup_directory is missing!")

        # Copying module to setup directory
        shutil.copy(fastapi_routes_filepath, 
                    os.path.join(setup_directory, "routes.py"))

        return True

    def run_app(self,
                description : dict = None, 
                middleware : dict = None,
                run_parameters : dict = None,
                package_names : list = None, 
                routes_paths : list = None,
                docs_paths : list = None):

        """
        Sets up FastAPI app with provided `description` and runs it with
        routes for selected `package_names` and `routes_paths` 
        with `run_parameters`.
        """

        if description is None:
            description = {}

        if package_names is None:
            package_names = []

        if routes_paths is None:
            routes_paths = []

        if run_parameters is None:
            run_parameters = {
                "host" : "0.0.0.0", 
                "port" : 8000
            }

        app = FastAPI(**description)

        if middleware is not None:
            app.add_middleware(
                CORSMiddleware,
                **middleware
            )

        if docs_paths:
            app = self._include_docs(
                app = app,
                docs_paths = docs_paths
            )

        app = self._include_package_routes(
            app = app, 
            package_names = package_names, 
            routes_paths = routes_paths)

        uvicorn.run(app, **run_parameters)

    def extract_routes_from_package(self, 
                              package_name : str, 
                              output_directory : str = '.', 
                              output_filepath : str = None):
        """
        Extracts the routes.py file from the specified package.
        """
        try:

            if output_directory is None:
                output_directory = '.'

            # Import the package
            package = importlib.import_module(package_name)
            
            # Get the package's directory
            package_dir = os.path.dirname(package.__file__)
            
            # Construct the path to routes.py
            routes_file_path = os.path.join(package_dir, 'routes.py')
            if not os.path.exists(routes_file_path):
                print(f"No routes.py found in package '{package_name}'.")
                return
            
            # Read the content of routes.py
            with open(routes_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Replace 'package_name.package_name' with 'package_name'
            content = content.replace(f'{package_name}.{package_name}', package_name)
            
            # Ensure the output directory exists
            os.makedirs(output_directory, exist_ok=True)
            
            # Write the modified content to a new file in the output directory
            if output_filepath is None:
                output_filepath = os.path.join(output_directory, f'{package_name}_route.py')

            with open(output_filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"Extracted routes.py from package '{package_name}' to '{output_filepath}'.")
        except ImportError:
            print(f"Package '{package_name}' not found.")
        except Exception as e:
            print(f"An error occurred: {e}")

@attr.s
class DependenciesAnalyser:

    package_name = attr.ib(default=True)
    base_mapping_filepath = attr.ib(default=None)
    package_licenses_filepath = attr.ib(default=None)
    allowed_licenses = attr.ib(default=[])

    package_licenses = attr.ib(default=None)

    standard_licenses = attr.ib(default=[
            "mit", "bsd-3-clause", "bsd-2-clause", "apache-2.0", 
            "gpl-3.0", "lgpl-3.0", "mpl-2.0", "agpl-3.0", "epl-2.0"
        ])

    logger = attr.ib(default=None)
    logger_name = attr.ib(default='Dependencies Analyser')
    loggerLvl = attr.ib(default=logging.DEBUG)
    logger_format = attr.ib(default=None)

    def __attrs_post_init__(self):
        self._initialize_logger()
        if self.allowed_licenses is None:
            self.allowed_licenses = self.standard_licenses
            self.allowed_licenses.append('-')

    def _initialize_logger(self):
        """
        Initialize a logger for the class instance based on the specified logging level and logger name.
        """

        if self.logger is None:
            logging.basicConfig(level=self.loggerLvl, format=self.logger_format)
            logger = logging.getLogger(self.logger_name)
            logger.setLevel(self.loggerLvl)

            self.logger = logger

    def _extract_dependencies_names(self, requirements : list):

        reqs = [req.split(" ")[0]\
            .split("==")[0]\
                .split("<=")[0]\
                    .split("<")[0]\
                        .split(">=")[0]\
                            .split(">")[0]\
                                .split(";")[0] \
            for req in requirements if 'extra ==' not in req]

        return reqs

    def _get_licenses(self, 
                      dependencies : list,
                      package_licenses : dict = None, 
                      normalize : bool = True):

        if package_licenses is None:
            package_licenses = self.package_licenses

        if package_licenses is None:
            package_licenses = self.load_package_mappings()

        licenses = {}
        for req in dependencies:
            try:
                license_ = self.get_package_metadata(req)['license_label']
                if license_:
                    if normalize:
                        license_ = self._normalize_license_label(license_)
                    else:
                        license_ = license_[0:50]
                else:
                    license_ = '-'
            except Exception as e:
                license_ = '-'

            if license_ == 'unknown':
                license_ = package_licenses.get(req, 'unknown')
            if license_ == '-':
                license_ = package_licenses.get(req, '-')

            licenses[req] = license_

        return licenses

    def _count_keys(self, d):
        if isinstance(d, dict):
            return len(d) + sum(self._count_keys(v) for v in d.values() if isinstance(v, dict))
        return 0

    def _apply_to_lists(self, data, func):
        for key, value in data.items():
            if isinstance(value, list):
                # Apply the function to the list
                data[key] = func(value)
            elif isinstance(value, dict):
                # Recursively go deeper into the dictionary
                self._apply_to_lists(value, func)
            # If value is neither list nor dict, do nothing

    def _extract_dependencies_layer(self, dependencies):

        if dependencies == []:
            return dependencies

        requirements_dict = self.extract_requirements_for_dependencies(
            dependencies = dependencies
        )
        dependencies_dict = {dep : self._extract_dependencies_names(reqs_) \
            for dep, reqs_ in requirements_dict.items()}

        return dependencies_dict

    def _flatten_dict_with_subtrees(self, d, parent_key=''):
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}.{k}" if parent_key else k
            # Add subtree or package
            items.append(new_key)  
            
            if isinstance(v, dict):
                # Recursively flatten subtrees
                items.extend(self._flatten_dict_with_subtrees(v, new_key)) 
            else:
                for item in v:
                    # Add individual packages
                    items.append(f"{new_key}.{item}") 
        return items

    def load_package_mappings(self,
                              mapping_filepath : str = None,
                              base_mapping_filepath : str = None):
        """
        Get file with mappings of package license labels.
        """

        if base_mapping_filepath is None:
            base_mapping_filepath = self.base_mapping_filepath

        if base_mapping_filepath is None:
            with pkg_resources.path('package_auto_assembler.artifacts', 
            'package_licenses.json') as path:
                base_mapping_filepath = path

            with open(base_mapping_filepath, 'r') as file:
                base_package_licenses = json.load(file)

        if mapping_filepath is None:
            mapping_filepath = self.package_licenses_filepath

        if mapping_filepath is None:
            self.logger.debug("No package mapping provided")
            package_licenses = {}
        else:
            with open(mapping_filepath, 'r') as file:
                package_licenses = json.load(file)

        base_package_licenses.update(package_licenses)

        self.package_licenses = base_package_licenses
            
        return base_package_licenses

    def extract_dependencies_tree(self, 
                                    package_name : str = None, 
                                    requirements : list = None,
                                    layers : int = 100):

        """
        Extracts dependencies tree for a package.
        """

        if package_name is None:
            package_name = self.package_name

        if package_name is None:
            raise ValueError(f"Provide package_name!")

        if requirements is None:

            requirements = self.get_package_requirements(
                package_name = package_name
            )

        if requirements:

            dependencies = self._extract_dependencies_names(
                requirements=requirements)

            dependencies_dict = self._extract_dependencies_layer(
                dependencies = dependencies)

            if layers == 1:
                return dependencies_dict


            for layer in range(layers):
                list_dim0 = self._count_keys(dependencies_dict)
                self._apply_to_lists(data = dependencies_dict, 
                            func = self._extract_dependencies_layer)

                list_dim = self._count_keys(dependencies_dict)
            
                if list_dim == list_dim0:
                    break
        else:
            dependencies_dict = {}


        return dependencies_dict

    def add_license_labels_to_dep_tree(self, 
                                        dependencies_tree : dict, 
                                        normalize : bool = True):

        """
        Adds license labels to dependencies tree.
        """

        flattened_tree_deps = self._flatten_dict_with_subtrees(
            dependencies_tree)

        tree_dep_license = {ft : self._get_licenses([ft.split('.')[-1]], 
        normalize = normalize)[ft.split('.')[-1]] \
            for ft in flattened_tree_deps}

        return tree_dep_license

    def find_unexpected_licenses_in_deps_tree(self,  
                                            tree_dep_license : dict,
                                            allowed_licenses : list = None,
                                            raise_error : bool = True):

        """
        Returns a dictionary of packages that contained unexpected license labels.
        If raise error is True, prints portion of dependencies tree.
        """

        if allowed_licenses is None:
            allowed_licenses = self.allowed_licenses

        
        out = {dep : license_label \
            for dep, license_label in tree_dep_license.items() \
                if license_label not in allowed_licenses}

        requirements = list(set([req.split('.')[0] for req in out \
            if req.split('.')[0] == req]))

        tree_missing_links_update = {req.split('.')[0] : '' \
            for req in out if req.split('.')[0] not in requirements} 

      
        for req_from_missing in tree_missing_links_update:

            tree_partials = {req : license_label \
                for req, license_label in out.items() \
                    if req.split('.')[0] == req_from_missing}

            for req_part in tree_partials:
                del out[req_part]
            
            out[req_from_missing] = tree_missing_links_update[req_from_missing]
            out.update(tree_partials)

        if raise_error and out != {}:
            self.print_flattened_tree(flattened_dict = out)
            raise Exception("Found unexpected licenses!")
        else:
            self.logger.info("No unexpected licenses found")

        return out

    def print_flattened_tree(self, flattened_dict):
        """
        Prints provided dependencies tree with provided values.
        """

        def recursive_build_tree(full_key, value, current_level):
            keys = full_key.split(".")
            for key in keys[:-1]:
                if key not in current_level:
                    current_level[key] = {}
                elif isinstance(current_level[key], str):
                    # If it's a string, convert it into a dictionary to store the nested structure
                    current_level[key] = {"_value": current_level[key]}
                current_level = current_level[key]
            # Store the value, handle if it's at a nested level or the root
            if keys[-1] in current_level and isinstance(current_level[keys[-1]], dict):
                current_level[keys[-1]]["_value"] = value
            else:
                current_level[keys[-1]] = value

        tree = {}
        for full_key, value in flattened_dict.items():
            recursive_build_tree(full_key, value, tree)

        def recursive_print(d, indent=0, is_last=False):
            for i, (key, value) in enumerate(d.items()):
                is_last_item = i == len(d) - 1
                prefix = "└── " if is_last_item else "├── "
                if isinstance(value, dict):
                    # Check if there is a _value to print as the value of this key
                    if "_value" in value:
                        print("    " * indent + prefix + key + f" : {value['_value']}")
                    else:
                        print("    " * indent + prefix + key + " : -")
                    recursive_print({k: v for k, v in value.items() if k != "_value"}, indent + 1, is_last_item)
                else:
                    print("    " * indent + prefix + key + f" : {value}")

        # Start printing the tree, avoiding extra _value printing at the root level
        for key, value in tree.items():
            if isinstance(value, dict) and "_value" in value:
                print(f"└── {key} : {value['_value']}")
                recursive_print({k: v for k, v in value.items() if k != "_value"}, indent=1)
            else:
                print(f"└── {key} : {value}")


    def extract_requirements_for_dependencies(self, dependencies : list):

        """
        Outputs a dictionary where key is dependency and value is 
        a list of requirements for that dependency.
        """
    
        requirements_dict = {dep : self.get_package_requirements(
            package_name = dep
        ) for dep in dependencies}

        return requirements_dict

    def filter_packages_by_tags(self, tags : list):

        """
        Uses list of provided tags to search though installed 
        dependencies and returns of names of those that match.
        """

        import pkg_resources
        matches = []
        for dist in pkg_resources.working_set:
            try:
                metadata_lines = dist.get_metadata_lines('METADATA')
                if all(any(tag in line for line in metadata_lines) for tag in tags):
                    matches.append((dist.project_name, dist.version))
            except (FileNotFoundError, KeyError):
                continue
        return matches


    def get_package_metadata(self, package_name : str = None):

        """
        Returns some preselected metadata fields if available, like:

            - keywords 
            - version
            - author
            - author_email
            - classifiers
            - paa_version
            - paa_cli
            - license_label

        for provided package name.
        """

        if package_name is None:
            package_name = self.package_name

        if package_name is None:
            raise ValueError(f"Provide package_name!")

        import pkg_resources
        dist = pkg_resources.get_distribution(package_name)
        metadata = dist.get_metadata_lines('METADATA')

        try:
            version = dist.version
        except Exception as e:
            version = None

        keywords = None
        author = None
        author_email = None
        paa_version = None
        paa_cli = False
        classifiers = []
        license_label = None

        for line in metadata:
            if line.startswith("Keywords:"):
                keywords = ast.literal_eval(line.split("Keywords: ")[1])
            if line.startswith("Author:"):
                author = line.split("Author: ")[1]
            if line.startswith("Author-email:"):
                author_email = line.split("Author-email: ")[1]
            if line.startswith("Classifier:"):
                classifiers.append(line.split("Classifier: ")[1])
            # if line.startswith("Classifier: PAA-Version ::"):
            #     paa_version = line.split("Classifier: PAA-Version :: ")[1]
            # if line.startswith("Classifier: PAA-CLI ::"):
            #     paa_cli = line.split("Classifier: PAA-CLI :: ")[1]
            if line.startswith("License:"):
                license_label = line.split("License: ")[1]

        return {'keywords' : keywords, 
                'version' : version, 
                'author' : author, 
                'author_email' : author_email, 
                'classifiers' : classifiers, 
                'paa_version' : paa_version, 
                'paa_cli' : paa_cli, 
                'license_label' : license_label}

    def get_package_requirements(self, package_name : str = None):

        """
        Returns a list of requirements for provided package name.
        """

        if package_name is None:
            package_name = self.package_name

        if package_name is None:
            raise ValueError(f"Provide package_name!")

        try:
            metadata = importlib.metadata.metadata(package_name)
            requirements = metadata.get_all("Requires-Dist", [])
            if requirements != []:
                requirements = requirements
        except Exception as e:
            self.logger.debug(f'No requirements found for {package_name}')
            requirements = []

        return requirements

    def _normalize_license_label(self, 
                                license_label : str,
                                standard_licenses : list = None):

        """
        For provided license label, attempts to match it with the following names:

            "mit", "bsd-3-clause", "bsd-2-clause", "apache-2.0", "gpl-3.0", "lgpl-3.0",
            "mpl-2.0", "agpl-3.0", "epl-2.0"
        
        and if nothing matches returns "unknown"
        """

        if standard_licenses is None:
            standard_licenses = self.standard_licenses

        if "bsd-3-clause" in standard_licenses:
            standard_licenses.append("new bsd")

        if license_label is None:
            return "unknown"
        
        # Normalize to lowercase
        normalized_label = license_label.lower()

        normalized_label = normalized_label.replace('software license', '')
        
        # Match with the highest similarity
        match = difflib.get_close_matches(normalized_label, standard_licenses, n=1, cutoff=0.4)

        license_label = match[0] if match else "unknown"

        # remapping licenses
        if license_label == "new bsd":
            license_label = "bsd-3-clause"

        return license_label

@attr.s
class PackageAutoAssembler:
    # pylint: disable=too-many-instance-attributes

    ## inputs
    module_name = attr.ib(type=str)

    ## paths
    module_filepath = attr.ib(type=str)
    cli_module_filepath = attr.ib(default=None)
    fastapi_routes_filepath = attr.ib(default=None)
    mapping_filepath = attr.ib(default=None)
    licenses_filepath = attr.ib(default=None)
    allowed_licenses = attr.ib(default=None)
    example_notebook_path = attr.ib(default=None)
    versions_filepath = attr.ib(default='./lsts_package_versions.yml')
    log_filepath = attr.ib(default='./version_logs.csv')
    setup_directory = attr.ib(default='./setup_dir')
    release_notes_filepath = attr.ib(default=None)
    config_filepath = attr.ib(default=None)
    cli_docs_filepath = attr.ib(default=None)

    artifacts_dir = attr.ib(default=None)
    dependencies_dir = attr.ib(default=None)
    docs_path = attr.ib(default=None)

    # optional parameters
    classifiers = attr.ib(default=['Development Status :: 3 - Alpha'])
    license_path = attr.ib(default=None)
    license_label = attr.ib(default=None)
    license_badge = attr.ib(default=None)
    docs_url = attr.ib(default=None)
    requirements_list = attr.ib(default=[])
    optional_requirements_list = attr.ib(default=[])
    python_version = attr.ib(default="3.8")
    version_increment_type = attr.ib(default="patch", type = str)
    default_version = attr.ib(default="0.0.1", type = str)
    kernel_name = attr.ib(default = 'python', type = str)
    max_git_search_depth = attr.ib(default=5, type = int)
    artifacts_filepaths = attr.ib(default=None, type = dict)
    docs_file_paths = attr.ib(default=None, type = dict)

    # switches
    add_artifacts = attr.ib(default=True, type = bool)
    remove_temp_files = attr.ib(default=True, type = bool)
    skip_deps_install = attr.ib(default=False, type = bool)
    check_vulnerabilities = attr.ib(default=True, type = bool)
    add_requirements_header = attr.ib(default=True, type = bool)
    use_commit_messages = attr.ib(default=True, type = bool)
    check_dependencies_licenses = attr.ib(default=False, type = bool)
    execute_readme_notebook = attr.ib(default=True, type = bool)
    add_mkdocs_site = attr.ib(default=True, type = bool)


    ## handler classes
    setup_dir_h_class = attr.ib(default=SetupDirHandler)
    version_h_class = attr.ib(default=VersionHandler)
    import_mapping_h_class = attr.ib(default=ImportMappingHandler)
    local_dependacies_h_class = attr.ib(default=LocalDependaciesHandler)
    requirements_h_class = attr.ib(default=RequirementsHandler)
    metadata_h_class = attr.ib(default=MetadataHandler)
    long_doc_h_class = attr.ib(default=LongDocHandler)
    cli_h_class = attr.ib(default=CliHandler)
    release_notes_h_class = attr.ib(default=ReleaseNotesHandler)
    dependencies_analyzer_h_class = attr.ib(default=DependenciesAnalyser)
    fastapi_h_class = attr.ib(default=FastApiHandler)
    artifacts_h_class = attr.ib(default=ArtifactsHandler)
    mkdocs_h_class = attr.ib(default=MkDocsHandler)

    ## handlers
    setup_dir_h = attr.ib(default = None, type = SetupDirHandler)
    version_h = attr.ib(default = None, type = VersionHandler)
    import_mapping_h = attr.ib(default = None, type=ImportMappingHandler)
    local_dependacies_h = attr.ib(default = None, type=LocalDependaciesHandler)
    requirements_h = attr.ib(default = None, type=RequirementsHandler)
    metadata_h = attr.ib(default = None, type=MetadataHandler)
    long_doc_h = attr.ib(default = None, type=LongDocHandler)
    cli_h = attr.ib(default = None, type=CliHandler)
    release_notes_h = attr.ib(default = None, type=ReleaseNotesHandler)
    dependencies_analyzer_h = attr.ib(default = None, type=DependenciesAnalyser)
    fastapi_h = attr.ib(default = None, type=FastApiHandler)
    artifacts_h = attr.ib(default = None, type=ArtifactsHandler)
    mkdocs_h = attr.ib(default = None, type=MkDocsHandler)

    ## output
    cli_metadata = attr.ib(default={}, type = dict)
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
            license_path = self.license_path,
            license_label = self.license_label,
            docs_url = self.docs_url,
            logger = self.logger)

    def _initialize_cli_handler(self):

        """
        Initialize cli handler with available parameters.
        """

        self.cli_h = self.cli_h_class(
            cli_module_filepath = self.cli_module_filepath,
            setup_directory = self.setup_directory,
            logger = self.logger)

    def _initialize_fastapi_handler(self):

        """
        Initialize fastapi handler with available parameters.
        """

        self.fastapi_h = self.fastapi_h_class(
            fastapi_routes_filepath = self.fastapi_routes_filepath,
            setup_directory = self.setup_directory,
            logger = self.logger)

    def _initialize_artifacts_handler(self):

        """
        Initialize artifacts handler with available parameters.
        """

        self.artifacts_h = self.artifacts_h_class(
            module_name = self.module_name,
            setup_directory = self.setup_directory,
            artifacts_dir = self.artifacts_dir,
            logger = self.logger)

    def _initialize_dep_analyser_handler(self):

        """
        Initialize cli handler with available parameters.
        """

        self.dependencies_analyzer_h = self.dependencies_analyzer_h_class(
            package_licenses_filepath = self.licenses_filepath,
            allowed_licenses = self.allowed_licenses,
            logger = self.logger)

    def _initialize_release_notes_handler(self, version : str = None):

        """
        Initialize release notes handler with available parameters.
        """

        if version is None:
            version = self.default_version

        self.release_notes_h = self.release_notes_h_class(
            filepath = self.release_notes_filepath,
            label_name = self.module_name,
            version = version,
            max_search_depth = self.max_git_search_depth,
            logger = self.logger)

    def _add_requirements(self,
                            module_filepath : str = None,
                            custom_modules : list = None,
                            import_mappings : str = None,
                            check_vulnerabilities : bool = None,
                            check_dependencies_licenses : bool = None,
                            add_header : bool = None):

        """
        Extract and add requirements.
        """

        if self.requirements_h is None:
            self._initialize_requirements_handler()

        if module_filepath is None:
            module_filepath = self.module_filepath

        if check_vulnerabilities is None:
            check_vulnerabilities = self.check_vulnerabilities

        if check_dependencies_licenses is None:
            check_dependencies_licenses = self.check_dependencies_licenses

        if import_mappings is None:
            import_mappings = self.import_mapping_h.load_package_mappings()

        if add_header is None:
            add_header = self.add_requirements_header

        custom_modules_list = self.requirements_h.list_custom_modules()

        if custom_modules:
            custom_modules_list += custom_modules

        self.logger.debug(f"Adding requirements from {module_filepath}")

        # extracting package requirements
        self.requirements_h.extract_requirements(
            package_mappings=import_mappings,
            module_filepath=module_filepath,
            custom_modules=custom_modules_list,
            add_header = add_header)

        self.requirements_list = self.requirements_h.requirements_list
        self.optional_requirements_list = self.requirements_h.optional_requirements_list

        if check_vulnerabilities:
            self.requirements_h.check_vulnerabilities()

        if check_dependencies_licenses:
            if self.dependencies_analyzer_h is None:
                self._initialize_dep_analyser_handler()

                edt = self.dependencies_analyzer_h.extract_dependencies_tree(
                    requirements = self.requirements_list + self.optional_requirements_list
                )

                edtl = self.dependencies_analyzer_h.add_license_labels_to_dep_tree(
                    dependencies_tree = edt
                )

                self.dependencies_analyzer_h.find_unexpected_licenses_in_deps_tree(
                    tree_dep_license = edtl
                )

    ###

    def add_metadata_from_module(self, module_filepath : str = None):

        """
        Add metadata extracted from the module.
        """

        self.logger.debug(f"Adding metadata ...")

        if self.metadata_h is None:
            self._initialize_metadata_handler()

        if module_filepath is None:
            module_filepath = self.module_filepath

        # extracting package metadata
        self.metadata = self.metadata_h.get_package_metadata(module_filepath = module_filepath)


    def add_metadata_from_cli_module(self,
                                     cli_module_filepath : str = None):

        """
        Add metadata extracted from the cli module.
        """

        self.logger.debug(f"Adding cli metadata ...")

        if self.metadata_h is None:
            self._initialize_metadata_handler()

        if cli_module_filepath is None:
            cli_module_filepath = self.cli_module_filepath

        if os.path.exists(cli_module_filepath) \
            and os.path.isfile(cli_module_filepath) \
                and self.metadata_h.is_metadata_available(
                    module_filepath = cli_module_filepath,
                    header_name = "__cli_metadata__"):

                # extracting package metadata
                self.cli_metadata = self.metadata_h.get_package_metadata(
                    module_filepath = cli_module_filepath,
                    header_name = "__cli_metadata__")



    def add_or_update_version(self,
                              module_name : str = None,
                              version_increment_type : str = None,
                              version : str = None,
                              versions_filepath : str = None,
                              log_filepath : str = None,
                              use_commit_messages : bool = None):

        """
        Increment version and creates entry in version logs.
        """

        self.logger.debug(f"Incrementing version ...")

        if self.version_h is None:
            self._initialize_version_handler()

        if use_commit_messages is None:
            use_commit_messages = self.use_commit_messages

        if use_commit_messages:
            self._initialize_release_notes_handler(version = version)
            self.release_notes_h.extract_version_update()
            
            version_increment_type = self.release_notes_h.version_update_label

            if self.release_notes_h.version != self.default_version:
                version = self.release_notes_h.version

        else:
            version_increment_type = None


        if module_name is None:
            module_name = self.module_name

        if version_increment_type is None:
            version_increment_type = self.version_increment_type

        if versions_filepath is None:
            versions_filepath = self.versions_filepath

        if log_filepath is None:
            log_filepath = self.log_filepath


        self.version_h.increment_version(package_name = module_name,
                                         version = version,
                                        increment_type = version_increment_type,
                                        default_version = version)
        version = self.version_h.get_version(package_name=module_name)

        self.metadata['version'] = version
        if self.release_notes_filepath:
            self.release_notes_h.version = self.metadata['version']

    def add_or_update_release_notes(self,
                              filepath : str = None,
                              version : str = None):

        """
        Increment version and creates entry in version logs.
        """

        self.logger.debug(f"Updating release notes ...")

        if self.release_notes_h is None:
            self._initialize_release_notes_handler()

        if filepath:
            self.release_notes_h.filepath = filepath
            self.release_notes_h._initialize_notes()

        if version:
            self.release_notes_h.version = version

        self.release_notes_h.create_release_note_entry()
        self.release_notes_h.save_release_notes()

    def prep_setup_dir(self, 
                       module_filepath : str = None,
                       module_docstring : str = None):

        """
        Prepare setup directory.
        """

        self.logger.debug(f"Preparing setup directory ...")

        if self.setup_dir_h is None:
            self._initialize_setup_dir_handler()

        if module_filepath is None:
            module_filepath = self.module_filepath

        if module_docstring is None:

            if self.long_doc_h is None:
                self._initialize_long_doc_handler()

            module_content = self.long_doc_h.read_module_content(filepath = module_filepath)

            module_docstring = self.long_doc_h.extract_module_docstring(module_content = module_content)

        # add module docstring
        self.setup_dir_h.docstring = module_docstring
        # create empty dir for setup
        self.setup_dir_h.flush_n_make_setup_dir()
        # copy module to dir
        self.setup_dir_h.copy_module_to_setup_dir()
        # copy license to dir
        self.setup_dir_h.copy_license_to_setup_dir()
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

        if dependencies_dir:
            self.logger.debug(f"Merging {main_module_filepath} with dependecies from {dependencies_dir} into {save_filepath}")

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
                                     custom_modules : list = None,
                                     import_mappings : str = None,
                                     check_vulnerabilities : bool = None,
                                     check_dependencies_licenses : bool = None,
                                     add_header : bool = None):

        """
        Extract and add requirements from the module.
        """

        self._add_requirements(
            module_filepath = module_filepath,
            custom_modules = custom_modules,
            import_mappings = import_mappings,
            check_vulnerabilities = check_vulnerabilities,
            check_dependencies_licenses = check_dependencies_licenses,
            add_header = add_header
        )

    def add_requirements_from_cli_module(self,
                                     module_name : str = None,
                                     cli_module_filepath : str = None,
                                     custom_modules : list = None,
                                     import_mappings : str = None,
                                     check_vulnerabilities : bool = None,
                                     check_dependencies_licenses : bool = None):

        """
        Extract and add requirements from the module.
        """

        if cli_module_filepath is None:
            cli_module_filepath = self.cli_module_filepath

        if module_name is None:
            module_name = self.module_name

        if custom_modules is None:
            custom_modules = []

        if os.path.exists(cli_module_filepath) \
                and os.path.isfile(cli_module_filepath):

            self._add_requirements(
                module_filepath = cli_module_filepath,
                custom_modules = custom_modules + [module_name],
                import_mappings = import_mappings,
                check_vulnerabilities = check_vulnerabilities,
                check_dependencies_licenses = check_dependencies_licenses,
                add_header = False
            )

    def add_requirements_from_api_route(self,
                                     module_name : str = None,
                                     fastapi_routes_filepath : str = None,
                                     custom_modules : list = None,
                                     import_mappings : str = None,
                                     check_vulnerabilities : bool = None,
                                     check_dependencies_licenses : bool = None):

        """
        Extract and add requirements from the module.
        """

        if fastapi_routes_filepath is None:
            fastapi_routes_filepath = self.fastapi_routes_filepath

        if module_name is None:
            module_name = self.module_name

        if custom_modules is None:
            custom_modules = []

        if os.path.exists(fastapi_routes_filepath) \
                and os.path.isfile(fastapi_routes_filepath):

            self._add_requirements(
                module_filepath = fastapi_routes_filepath,
                custom_modules = custom_modules + [module_name],
                import_mappings = import_mappings,
                check_vulnerabilities = check_vulnerabilities,
                check_dependencies_licenses = check_dependencies_licenses,
                add_header = False
            )

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

        self.logger.info(f"Adding README from {example_notebook_path} to {output_path}")

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

    def make_mkdocs_site(self):

        """
        Use provided docs to generate simple mkdocs site. 
        """

        if self.add_mkdocs_site:

            if self.mkdocs_h is None:

                package_name = self.module_name

                module_content = LongDocHandler().read_module_content(
                    filepath=self.module_filepath)
                docstring = LongDocHandler().extract_module_docstring(
                    module_content=module_content)
                pypi_link = LongDocHandler().get_pypi_badge(
                    module_name=package_name)

                if (self.docs_path is not None) \
                    and (os.path.exists(self.docs_path)):
                    doc_files = os.listdir(self.docs_path)
                else:
                    doc_files = []
                
                docs_file_paths = {}

                package_docs = [doc_file for doc_file in doc_files \
                    if doc_file.startswith(package_name)]

                for package_doc in package_docs:

                    if package_doc == f"{package_name}.md":
                        docs_file_paths[os.path.join(self.docs_path,package_doc)] = "usage-examples.md"
                    else:
                        docs_file_paths[os.path.join(self.docs_path,package_doc)] = package_doc

                if self.docs_file_paths:
                    docs_file_paths.update(self.docs_file_paths)

                if (self.release_notes_filepath is not None) \
                    and os.path.exists(self.release_notes_filepath):
                    docs_file_paths[self.release_notes_filepath] = "release-notes.md"

                if (self.cli_docs_filepath is not None) \
                    and os.path.exists(self.cli_docs_filepath):
                    docs_file_paths[self.cli_docs_filepath] = "cli.md"

            
                self.mkdocs_h = MkDocsHandler(
                    project_name = f"{package_name}_temp_mkdocs",
                    package_name = package_name,
                    docs_file_paths = docs_file_paths,
                    module_docstring = docstring,
                    pypi_badge = pypi_link,
                    license_badge=self.license_badge)

            self.mkdocs_h.create_mkdocs_dir()
            self.mkdocs_h.move_files_to_docs()
            self.mkdocs_h.generate_markdown_for_images()
            self.mkdocs_h.create_index()
            self.mkdocs_h.create_mkdocs_yml()
            self.mkdocs_h.build_mkdocs_site()

            if self.artifacts_filepaths is None:
                self.artifacts_filepaths = {}

            self.artifacts_filepaths['mkdocs'] = f"{package_name}_temp_mkdocs"

    def prepare_artifacts(self, artifacts_filepaths : dict = None):

        """
        Add artifacts to setup directory and its manifest.
        """

        if self.artifacts_h is None:
            self._initialize_artifacts_handler()

        if artifacts_filepaths is None:
            artifacts_filepaths = self.artifacts_filepaths

        if artifacts_filepaths is None:
            artifacts_filepaths = {}

        additional_artifacts_filepaths = self.artifacts_h.load_additional_artifacts()

        artifacts_filepaths.update(additional_artifacts_filepaths)

        artifacts_filepaths_m = {name : import_path \
            for name, import_path in artifacts_filepaths.items() if name == 'mkdocs'}

        artifacts_filepaths_m.update({os.path.join('artifacts', name) : import_path \
            for name, import_path in artifacts_filepaths.items() if name != 'mkdocs'})
        
        artifacts_filepaths = artifacts_filepaths_m

        if self.add_artifacts:

            if (self.log_filepath is not None \
                and os.path.exists(self.log_filepath)):
                artifacts_filepaths['.paa.tracking/version_logs.csv'] = self.log_filepath

            if (self.release_notes_filepath is not None \
                and os.path.exists(self.release_notes_filepath)):
                artifacts_filepaths['.paa.tracking/release_notes.md'] = self.release_notes_filepath

            if (self.versions_filepath is not None \
                and os.path.exists(self.versions_filepath)):
                artifacts_filepaths['.paa.tracking/lsts_package_versions.yml'] = self.versions_filepath

            if (self.example_notebook_path is not None \
                and os.path.exists(self.example_notebook_path)):
                artifacts_filepaths['.paa.tracking/notebook.ipynb'] = self.example_notebook_path

            if (self.mapping_filepath is not None \
                and os.path.exists(self.mapping_filepath)):
                artifacts_filepaths['.paa.tracking/package_mapping.json'] = self.mapping_filepath

            if (self.licenses_filepath is not None \
                and os.path.exists(self.licenses_filepath)):
                artifacts_filepaths['.paa.tracking/package_licenses.json'] = self.licenses_filepath

            if (self.config_filepath is not None \
                and os.path.exists(self.config_filepath)):
                artifacts_filepaths['.paa.tracking/.paa.config'] = self.config_filepath

        self.artifacts_h.make_manifest(
            artifacts_filepaths = artifacts_filepaths
        )

        self.artifacts_filepaths = self.artifacts_h.artifacts_filepaths

    def prep_setup_file(self,
                       module_name : str = None,
                       cli_module_filepath : str = None,
                       fastapi_routes_filepath : str = None,
                       metadata : dict = None,
                       cli_metadata : dict = None,
                       requirements : list = None,
                       optional_requirements : list = None,
                       classifiers : list = None,
                       module_filepath : str = None,
                       module_docstring : str = None,
                       add_artifacts : bool = None,
                       artifacts_filepaths : dict = None):

        """
        Assemble setup.py file.
        """

        
        if self.setup_dir_h is None:
            self._initialize_setup_dir_handler()

        if cli_module_filepath is None:
            cli_module_filepath = self.cli_module_filepath

        if fastapi_routes_filepath is None:
            fastapi_routes_filepath = self.fastapi_routes_filepath

        if metadata is None:
            metadata = self.metadata

        if cli_metadata is None:
            cli_metadata = self.cli_metadata

        if requirements is None:
            requirements = self.requirements_list

        if optional_requirements is None:
            optional_requirements = self.optional_requirements_list

        if classifiers is None:
            classifiers = self.classifiers

        if module_filepath is None:
            module_filepath = self.module_filepath

        if module_name is None:
            module_name = self.module_name

        if add_artifacts is None:
            add_artifacts = self.add_artifacts

        if artifacts_filepaths is None:
            artifacts_filepaths = self.artifacts_filepaths

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

        if fastapi_routes_filepath is not None \
            and os.path.exists(fastapi_routes_filepath) \
                and os.path.isfile(fastapi_routes_filepath):

            if self.fastapi_h is None:
                self._initialize_fastapi_handler()

            add_fastapi = self.fastapi_h.prepare_routes(
                fastapi_routes_filepath = fastapi_routes_filepath
            )

    
        self.logger.info(f"Preparing setup file for {module_name.replace('_','-')} package ...")

        # create setup.py
        self.setup_dir_h.write_setup_file(module_name = module_name,
                                          module_docstring = module_docstring,
                                          metadata = metadata,
                                          cli_metadata = cli_metadata,
                                          requirements = requirements,
                                          optional_requirements = optional_requirements,
                                          classifiers = classifiers,
                                          add_cli_tool = add_cli_tool,
                                          add_artifacts = add_artifacts,
                                          artifacts_filepaths = artifacts_filepaths)

        if self.artifacts_h is not None:
            self.artifacts_h.write_mafifest()

    
    def make_package(self,
                     setup_directory : str = None):

        """
        Create a package.
        """

        if setup_directory is None:
            setup_directory = self.setup_directory

        self.logger.info(f"Making package from {setup_directory} ...")

        # Define the command as a list of arguments
        command = ["python", os.path.join(setup_directory, "setup.py"), "sdist", "bdist_wheel"]

        # Execute the command
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        return result

    def test_install_package(self,
                             module_name : str = None,
                             remove_temp_files : bool = None,
                             skip_deps_install : bool = None):

        """
        Test install package to environment and optional remove temp files.
        """

        if module_name is None:
            module_name = self.module_name

        if remove_temp_files is None:
            remove_temp_files = self.remove_temp_files

        if skip_deps_install is None:
            skip_deps_install = self.skip_deps_install

        self.logger.info(f"Test installing {module_name} package ...")

        # Reinstall the module from the wheel file
        wheel_files = [f for f in os.listdir('dist') if f.endswith('-py3-none-any.whl')]

        for wheel_file in wheel_files:
            list_of_cmds = [sys.executable, 
                            "-m", "pip", "install", "--force-reinstall"]

            if skip_deps_install:
                list_of_cmds.append("--no-deps")

            list_of_cmds.append(os.path.join('dist', wheel_file))

            subprocess.run(list_of_cmds, check=True)

        if remove_temp_files:
            # Clean up the build directories and other generated files
            shutil.rmtree('build', ignore_errors=True)
            shutil.rmtree('dist', ignore_errors=True)
            shutil.rmtree(module_name, ignore_errors=True)
            shutil.rmtree(f"{module_name}.egg-info", ignore_errors=True)

            if os.path.exists(f"{module_name}_temp_mkdocs"):
                shutil.rmtree(f"{module_name}_temp_mkdocs", ignore_errors=True)

