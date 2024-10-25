import logging
import os
import json
import attr #>=22.2.0
import importlib
import importlib.metadata
import importlib.resources as pkg_resources

@attr.s
class ImportMappingHandler:

    """
    A tool to access install-import mapping for packages.
    """

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


            # with pkg_resources.path('package_auto_assembler','.') as path:
            #     paa_path = path
            paa_path = pkg_resources.files('package_auto_assembler')

            if 'artifacts' in os.listdir(paa_path):

                with pkg_resources.path('package_auto_assembler.artifacts',
                'package_mapping.json') as path:
                    base_mapping_filepath = path

        if (mapping_filepath is not None) \
            and os.path.exists(mapping_filepath):

            with open(mapping_filepath, 'r') as file:
                mapping_file = json.load(file)
        else:
            mapping_file = {}

        if (base_mapping_filepath is not None) and \
            os.path.exists(base_mapping_filepath):

            with open(base_mapping_filepath, 'r') as file:
                base_mapping_file = json.load(file)
        else:
            base_mapping_file = {}

        base_mapping_file.update(mapping_file)

        return base_mapping_file
