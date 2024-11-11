import logging
import os
import csv
import yaml
from datetime import datetime
import pandas as pd
import re
import attr #>=22.2.0

@attr.s
class VersionHandler:

    """
    Contains set of tools to iterate version of a package.
    """

    versions_filepath = attr.ib()
    log_filepath = attr.ib()

    default_version = attr.ib(default="0.0.1")
    read_files = attr.ib(default=True)

    log_file = attr.ib(default=True)
    csv_writer = attr.ib(default=True)

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
        with open(self.versions_filepath, 'w', encoding = "utf-8"):
            pass

    def _save_versions(self):

        """
        Persist versions in yaml file.
        """

        with open(self.versions_filepath, 'w', encoding = "utf-8") as file:
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