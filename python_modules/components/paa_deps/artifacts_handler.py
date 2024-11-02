import logging
import os
import shutil
import attr #>=22.2.0
import requests
import importlib
import importlib.metadata
import importlib.resources as pkg_resources
from pathlib import Path

@attr.s
class ArtifactsHandler:

    """
    Contains set of tools to prepare artifacts for packaging.
    """

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

    def _get_artifact_links(self,
                            artifact_name : str,
                            artifacts_filepath : str,
                            use_artifact_name : bool = True):

        link_artifacts_filepaths = {}

        dir_skip = len(Path(artifact_name).parts) +1

        link_files = [f for f in Path(artifacts_filepath).rglob('*.link')]

        for lf in link_files:
            if use_artifact_name:
                cleaned_lf = str(os.path.join(
                    artifact_name,Path(*lf.parts[dir_skip:])))
            else:
                cleaned_lf = str(lf)

            link_artifacts_filepaths[cleaned_lf] = str(lf)

        return link_artifacts_filepaths

    def _check_file_exists(self, url : str):

        try:
            response = requests.head(url, allow_redirects=True)
            # Status codes 200 (OK) or 302/301 (redirect) indicate the file exists
            if response.status_code == 200:
                return True
            else:
                return False
        except requests.RequestException as e:
            print(f"Error occurred: {e}")
            return False

    def load_additional_artifacts(self, artifacts_dir : str = None):

        """
        Load artifacts filepath from provided folder.
        """

        if artifacts_dir is None:
            artifacts_dir = self.artifacts_dir

        artifacts_filepaths = {}

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
        if not os.path.exists(os.path.join(
                setup_directory, ".paa.tracking")):
            os.makedirs(os.path.join(setup_directory,'.paa.tracking'))
        if not os.path.exists(os.path.join(
                setup_directory, ".paa.tracking", 'python_modules')):
            os.makedirs(os.path.join(setup_directory,'.paa.tracking', 'python_modules'))
        if not os.path.exists(os.path.join(
                setup_directory, ".paa.tracking", 'python_modules','components')):
            os.makedirs(os.path.join(setup_directory,'.paa.tracking', 'python_modules','components'))

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
        link_artifacts_filepaths = {}

        for artifact_name, artifacts_filepath in artifacts_filepaths.items():

            if os.path.isdir(artifacts_filepath):

                link_artifacts_filepaths = self._get_artifact_links(
                    artifact_name = artifact_name,
                    artifacts_filepath = artifacts_filepath
                )

        artifacts_filepaths.update(link_artifacts_filepaths)

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
            elif artifacts_filepath.endswith(".link"):

                try:

                    # Open the file and read the content
                    with open(artifacts_filepath, 'r') as file:
                        artifacts_url = file.readline().strip()

                    # Add link file
                    shutil.copy(artifacts_filepath,
                        os.path.join(setup_directory, artifact_name))

                    manifest_lines.append(f"include {module_name}/{artifact_name} \n")

                    updated_artifacts_filepaths[artifact_name] = artifacts_filepath

                    artifact_name = artifact_name.replace(".link", "")

                    # Make a GET request to download the file
                    response = requests.get(artifacts_url, stream=True)

                    # Open the file in binary mode and write the content to it
                    with open(os.path.join(setup_directory, artifact_name), 'wb') as file:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:  # Filter out keep-alive chunks
                                file.write(chunk)

                    manifest_lines.append(f"include {module_name}/{artifact_name} \n")

                except Exception as e:
                    self.logger.warning(f"Failed to download {artifacts_filepath} artifact!")
            elif artifact_name.endswith(".link"):

                try:

                    # Open the file in binary mode and write the content to it
                    with open(os.path.join(setup_directory, artifact_name), 'w') as file:
                        file.write(f"{artifacts_filepath}")

                    manifest_lines.append(f"include {module_name}/{artifact_name} \n")
                except Exception as e:
                    self.logger.warning(f"Failed to save {artifacts_filepath} link as artifact!")


            else:
                directory = Path(os.path.join(setup_directory, artifact_name)).parent
                directory.mkdir(parents=True, exist_ok=True)
                
                shutil.copy(artifacts_filepath,
                    os.path.join(setup_directory, artifact_name))
                manifest_lines.append(f"include {module_name}/{artifact_name} \n")

            updated_artifacts_filepaths[artifact_name] = artifacts_filepath

        manifest_lines.append(f"include {module_name}/{'.paa.tracking/.paa.version'} \n")
        updated_artifacts_filepaths['.paa.tracking/.paa.version'] = os.path.join(setup_directory,'.paa.tracking','.paa.version')

        self.artifacts_filepaths = updated_artifacts_filepaths
        self.manifest_lines = manifest_lines

    def show_module_links(self,  module_name : str = None):

        """
        Show link available within a package.
        """

        if module_name is None:
            module_name = self.module_name

        package_path = pkg_resources.files(module_name)

        link_for_artifacts = {}
        link_availability = {}

        if os.path.exists(package_path):

            link_artifacts_filepaths = self._get_artifact_links(
                artifact_name = 'artifacts',
                artifacts_filepath = os.path.join(package_path, 'artifacts')
            )

            for artifact_name, artifacts_filepath in link_artifacts_filepaths.items():

                try:

                    # Open the file and read the content
                    with open(artifacts_filepath, 'r') as file:
                        artifacts_url = file.readline().strip()

                    link_for_artifacts[os.path.basename(artifact_name)] = artifacts_url
                    link_availability[os.path.basename(artifact_name)] = self._check_file_exists(artifacts_url)

                except Exception as e:
                    self.logger.warning(f"Failed to read {artifacts_filepath} link!")

        else:
            raise Exception(f"Package {module_name} was not found!")

        return link_for_artifacts, link_availability

    def refresh_artifacts_from_link(self, module_name : str = None):

        """
        Refresh artifacts based on link in packaged artifacts
        """

        if module_name is None:
            module_name = self.module_name

        package_path = pkg_resources.files(module_name)

        failed_refreshes = 0

        if os.path.exists(package_path):

            link_artifacts_filepaths = self._get_artifact_links(
                artifact_name = 'artifacts',
                artifacts_filepath = os.path.join(package_path, 'artifacts'),
                use_artifact_name = False
            )

            for artifact_name, artifacts_filepath in link_artifacts_filepaths.items():

                try:

                    # Open the file and read the content
                    with open(artifacts_filepath, 'r') as file:
                        artifacts_url = file.readline().strip()

                    artifact_name = artifact_name.replace(".link", "")

                    # Make a GET request to download the file
                    response = requests.get(artifacts_url, stream=True)

                    # Open the file in binary mode and write the content to it
                    with open(os.path.join(package_path, artifact_name), 'wb') as file:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:  # Filter out keep-alive chunks
                                file.write(chunk)

                except Exception as e:
                    failed_refreshes += 1
                    self.logger.warning(
                        f"Failed to refresh {os.path.basename(artifact_name)} with  {artifacts_url}!")

        else:
            raise Exception(f"Package {module_name} was not found!")

        return failed_refreshes

    def write_mafifest(self):

        """
        Write prepared manifest to setup dir.
        """

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