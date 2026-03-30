import logging
import os
import shutil
import attrs
import attrsx

@attrsx.define
class TestsHandler:

    """
    Prepares tests for package-auto-assembler.
    """

    # inputs
    tests_dir = attrs.field()
    setup_directory = attrs.field()

    # processed
    logger = attrs.field(default=None)
    logger_name = attrs.field(default='Tests Handler')
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

    def prepare_tests(self,
                       tests_dir: str = None,
                       setup_directory : str = None):

        """
        Prepare drawio file for packaging.
        """

        if tests_dir is None:
            tests_dir = self.tests_dir

        if setup_directory is None:
            setup_directory = self.setup_directory

        # Copying module to setup directory
        if tests_dir and os.path.exists(tests_dir):
            
            shutil.copytree(tests_dir, os.path.join(
                setup_directory,"tests"))

        return True
