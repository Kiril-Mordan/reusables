import logging
import os
import json
import importlib
import importlib.metadata
import importlib.resources as pkg_resources
import attrs
import attrsx

@attrsx.define
class ImportMappingHandler:

    """
    A tool to access install-import mapping for packages.

    Usage example:
    ```python
    imh = ImportMappingHandler(mapping_filepath=".paa/package_mapping.json")
    package_mappings = imh.load_package_mappings()
    # example: {"yaml": "pyyaml", "PIL": "Pillow"}
    ```
    """

    mapping_filepath = attrs.field(default = None)
    base_mapping_filepath = attrs.field(default = None)

    logger = attrs.field(default=None)
    logger_name = attrs.field(default='Package Import Mapping Handler')
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


            # with pkg_resources.path('package_auto_assembler','.') as path:
            #     paa_path = path
            paa_path = pkg_resources.files('package_auto_assembler')

            if 'artifacts' in os.listdir(paa_path):

                with pkg_resources.path('package_auto_assembler.artifacts',
                'package_mapping.json') as path:
                    base_mapping_filepath = path

        if (mapping_filepath is not None) \
            and os.path.exists(mapping_filepath):

            with open(mapping_filepath, 'r',
            encoding = "utf-8") as file:
                mapping_file = json.load(file)
        else:
            mapping_file = {}

        if (base_mapping_filepath is not None) and \
            os.path.exists(base_mapping_filepath):

            with open(base_mapping_filepath, 'r',
            encoding = "utf-8") as file:
                base_mapping_file = json.load(file)
        else:
            base_mapping_file = {}

        base_mapping_file.update(mapping_file)

        return base_mapping_file
