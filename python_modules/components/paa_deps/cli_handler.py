import logging
import os
import shutil
import attr #>=22.2.0

@attr.s
class CliHandler:

    """
    Prepares cli tool for package-auto-assembler.
    """

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