import logging
import ast
import attrs
import attrsx

@attrsx.define
class MetadataHandler:

    """
    Extracts and checks package metadata.

    Usage example:
    ```python
    mh = MetadataHandler(module_filepath="python_modules/your_package.py")
    if mh.is_metadata_available():
        package_metadata = mh.get_package_metadata()
    ```
    """

    module_filepath = attrs.field(default=None)
    header_name = attrs.field(default="__package_metadata__")

    metadata_status = attrs.field(factory=dict, type=dict)

    logger = attrs.field(default=None)
    logger_name = attrs.field(default='Package Metadata Handler')
    loggerLvl = attrs.field(default=logging.INFO)
    logger_format = attrs.field(default=None)

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

    def _read_metadata_block(self, module_filepath: str, header_name: str) -> str:
        """
        Read raw metadata assignment block from module source.
        """

        metadata_str = ""
        inside_metadata = False
        expecting_closing_brackets = 0

        with open(module_filepath, 'r', encoding='utf-8') as file:
            for line in file:

                if '{' in line:
                    expecting_closing_brackets += 1
                if '}' in line:
                    expecting_closing_brackets -= 1

                if f'{header_name} =' in line:
                    inside_metadata = True
                    metadata_str = line.split('#')[0]  # Ignore comments
                elif inside_metadata:
                    metadata_str += line.split('#')[0]  # Ignore comments
                    if ('}' in line) and (expecting_closing_brackets <= 0):
                        break

        return metadata_str

    def _set_metadata_status(self, header_name: str, value: bool) -> None:
        """
        Update metadata presence cache in a pylint-friendly way.
        """
        status = dict(self.metadata_status or {})
        status[header_name] = value
        self.metadata_status = status


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
            with open(module_filepath, 'r', encoding='utf-8') as file:
                for line in file:
                    # Check if the line defines __package_metadata__
                    if line.strip().startswith(f"{header_name} ="):
                        self._set_metadata_status(header_name, True)
                        return True
            self._set_metadata_status(header_name, False)
            return False
        except FileNotFoundError:
            self._set_metadata_status(header_name, False)
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

        try:
            metadata_str = self._read_metadata_block(
                module_filepath=module_filepath,
                header_name=header_name
            )

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
        except (OSError, ValueError, TypeError, SyntaxError) as e:
            return f"An error occurred: {e}"
