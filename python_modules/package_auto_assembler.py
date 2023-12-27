import re
import os
import json
import importlib.util
from stdlib_list import stdlib_list
import attr

import yaml
import os
import logging
from datetime import datetime
import csv

import subprocess


@attr.s
class PackageAutoAssembler:
    # pylint: disable=too-many-instance-attributes


    versions_filepath = attr.ib(default='./lsts_package_versions.yml')
    log_filepath = attr.ib(default='./version_logs.csv')

    setup_dir = attr.ib(default='./setup_dir')


    package_result = attr.ib(init=False)

    def add_or_update_version(self,
                              version : str = None,
                              versions_filepath : str = None,
                              log_filepath : str = None):

        if versions_filepath is None:
            versions_filepath = self.versions_filepath

        if log_filepath is None:
            log_filepath = self.log_filepath

    def write_setup_file(self,
                         module_name,
                         metadata,
                         install_requires,
                         classifiers,
                         setup_dir : str = None):

        if setup_dir is None:
            setup_dir = self.setup_dir

        metadata_str = ', '.join([f'{key}="{value}"' for key, value in metadata.items()])
        setup_content = f"""from setuptools import setup

    setup(
        name="{module_name}",
        packages=["{module_name}"],
        install_requires={install_requires},
        classifiers={classifiers},
        {metadata_str}
    )
        """
        with open('setup_dir/setup.py', 'w') as file:
            file.write(setup_content)

    def make_package(self):

        # Define the command as a list of arguments
        command = ["python", "setup_dir/setup.py", "sdist", "bdist_wheel"]

        # Execute the command
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


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
        self.versions = self._read_versions()
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

    def log_version_update(self, package_name, new_version):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.csv_writer.writerow([timestamp, package_name, new_version])
        self.log_file.flush()  # Ensure data is written to the file

    # Remember to close the log file when done
    def close_log_file(self):
        self.log_file.close()

    def _read_versions(self):
        with open(self.versions_filepath, 'r') as file:
            return yaml.safe_load(file) or {}

    def get_version(self, package_name):
        return self.versions.get(package_name)

    def update_version(self, package_name, new_version):
        self.versions[package_name] = new_version
        self._save()
        self.log_version_update(package_name, new_version)

    def add_package(self, package_name, version):
        if package_name not in self.versions:
            self.versions[package_name] = version
            self._save()
            self.log_version_update(package_name, version)

    def _save(self):
        with open(self.versions_filepath, 'w') as file:
            yaml.safe_dump(self.versions, file)

    def __str__(self):
        return yaml.safe_dump(self.versions)

    def _parse_version(self, version):
        major, minor, patch = map(int, version.split('.'))
        return major, minor, patch

    def _format_version(self, major, minor, patch):
        return f"{major}.{minor}.{patch}"

    def increment_major(self, package_name):
        if package_name in self.versions:
            prev_version = self.versions[package_name]
            major, minor, patch = self._parse_version(prev_version)
            major += 1
            # Reset minor and patch versions when major is incremented
            new_version = self._format_version(major, 0, 0)
            self.update_version(package_name, new_version)

            self.logger.debug(f"Incremented major of {package_name} \
                from {prev_version} to {new_version}")

    def increment_minor(self, package_name):
        if package_name in self.versions:
            prev_version = self.versions[package_name]
            major, minor, patch = self._parse_version(prev_version)
            minor += 1
            # Reset patch version when minor is incremented
            new_version = self._format_version(major, minor, 0)
            self.update_version(package_name, new_version)

            self.logger.debug(f"Incremented minor of {package_name} \
                from {prev_version} to {new_version}")

    def increment_patch(self, package_name):
        if package_name in self.versions:
            prev_version = self.versions[package_name]
            major, minor, patch = self._parse_version(prev_version)
            patch += 1
            new_version = self._format_version(major, minor, patch)
            self.update_version(package_name, new_version)

            self.logger.debug(f"Incremented patch of {package_name} \
                from {prev_version} to {new_version}")
        else:
            self.logger.warning(f{})

@attr.s
class ImportMappingHandler:

    mapping_filepath = attr.ib()

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

    custom_modules_filepath = attr.ib()
    python_version = attr.ib(default='3.8')


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


    def get_package_metadata(self, module_name, modules_path):
        module_path = os.path.join(modules_path, module_name + '.py')
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.__package_metadata__




