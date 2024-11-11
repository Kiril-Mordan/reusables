import logging
import subprocess
import os
import sys
import shutil
import importlib
import attr #>=22.2.0

@attr.s
class StreamlitHandler:

    """
    Contains set of tools to prepare and handle streamlit code for packages.
    """

    # inputs
    streamlit_filepath = attr.ib(default = None)
    setup_directory = attr.ib(default = None)

    package_name = attr.ib(default = None)

    config_path = attr.ib(default = '.paa.streamlit.config')

    # processed
    logger = attr.ib(default=None)
    logger_name = attr.ib(default='Streamlit Handler')
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

    def _prep_custom_config(self, config_path : str):

        # Define Streamlit's default configuration directory
        streamlit_config_dir = os.path.expanduser("~/.streamlit")
        os.makedirs(streamlit_config_dir, exist_ok=True)

        # Define paths for the temporary custom config and the final config
        final_config_path = os.path.join(streamlit_config_dir, "config.toml")
        backup_config_path = os.path.join(streamlit_config_dir, "config_backup.toml")

        # If backup does not exist, make backup    
        if (not os.path.exists(backup_config_path)) and os.path.exists(final_config_path):

            os.rename(final_config_path, backup_config_path)

        # Move provided config to streamlit dir
        shutil.copy(config_path, final_config_path)

        

    def prepare_streamlit(self,
                       streamlit_filepath: str = None,
                       setup_directory : str = None):

        """
        Prepare fastapi routes for packaging.
        """

        if streamlit_filepath is None:
            streamlit_filepath = self.streamlit_filepath

        if setup_directory is None:
            setup_directory = self.setup_directory

        if streamlit_filepath is None:
            raise ImportError("Parameter streamlit_filepath is missing!")

        if setup_directory is None:
            raise ImportError("Parameter setup_directory is missing!")

        # Copying module to setup directory
        shutil.copy(streamlit_filepath,
                    os.path.join(setup_directory, "streamlit.py"))

        return True

    def run_app(self, 
                package_name : str = None,
                streamlit_filepath : str = None,
                config_path : str = None,
                host : str = None,
                port : str = None):

        """
        Runs streamlit application from a paa package.
        """

        if streamlit_filepath is None:
            streamlit_filepath = self.streamlit_filepath

        if config_path is None:
            config_path = self.config_path

        if config_path:
            self._prep_custom_config(config_path = config_path)
            
        if package_name is None:
            package_name = self.package_name

        if package_name:

            try:
                package_name = package_name.replace('-','_')

                # Import the package
                package = importlib.import_module(package_name)

                # Get the package's directory
                package_dir = os.path.dirname(package.__file__)

                # Construct the path to routes.py
                streamlit_filepath = os.path.join(package_dir, 'streamlit.py')

            except ImportError as e:
                print(e)
                self.logger.error(f"Error importing streamlit from {package_name}: {e}")
                sys.exit(1)

        if not os.path.exists(streamlit_filepath):
            raise ValueError(f"Provide valid streamlit_filepath, {streamlit_filepath} not found!")

        streamlit_run_command = ["streamlit", "run", streamlit_filepath]

        if host:
            streamlit_run_command.append(f"--server.address={host}")

        if port:
            streamlit_run_command.append(f"--server.port={port}")

        # Run the Streamlit app with the custom configuration
        subprocess.run(streamlit_run_command, check = True)

    def extract_streamlit_from_package(self,
                            package_name : str,
                            output_directory : str = None,
                            output_filepath : str = None):

        """
        Extracts `streamlit.py` file from the specified package.
        """

        try:

            if output_directory is None:
                output_directory = '.'

            # Import the package
            package = importlib.import_module(package_name)

            # Get the package's directory
            package_dir = os.path.dirname(package.__file__)

            # Construct the path to routes.py
            streamlit_file_path = os.path.join(package_dir, 'streamlit.py')
            if not os.path.exists(routes_file_path):
                print(f"No streamlit.py found in package '{package_name}'.")
                return

            # Read the content of routes.py
            with open(streamlit_file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Replace 'package_name.package_name' with 'package_name'
            content = content.replace(f'{package_name}.{package_name}', package_name)

            # Ensure the output directory exists
            os.makedirs(output_directory, exist_ok=True)

            # Write the modified content to a new file in the output directory
            if output_filepath is None:
                output_filepath = os.path.join(output_directory, f'{package_name}_streamlit.py')

            with open(output_filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            self.logger.info(f"Extracted streamlit.py from package '{package_name}' to '{output_filepath}'.")
        except ImportError:
            print(f"Package '{package_name}' not found.")
        except Exception as e:
            print(f"An error occurred: {e}")
