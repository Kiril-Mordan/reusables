import logging
import ast
import attr #>=22.2.0

@attr.s
class MetadataHandler:

    """
    Extracts and checks package metadata.
    """

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
