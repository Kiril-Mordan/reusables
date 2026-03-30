import logging
import os
import shutil
import attrs
import attrsx

@attrsx.define
class DrawioHandler:

    """
    Prepares drawio files for package-auto-assembler.
    """

    # inputs
    drawio_filepath = attrs.field()
    setup_directory = attrs.field()

    # processed
    logger = attrs.field(default=None)
    logger_name = attrs.field(default='Drawio Handler')
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

    def prepare_drawio(self,
                       drawio_filepath: str = None,
                       setup_directory : str = None):

        """
        Prepare drawio file for packaging.
        """

        if drawio_filepath is None:
            drawio_filepath = self.drawio_filepath

        if setup_directory is None:
            setup_directory = self.setup_directory

        # Copying module to setup directory
        if (drawio_filepath is not None) and os.path.exists(drawio_filepath):
            
            if not os.path.exists(os.path.join(
                setup_directory, ".paa.tracking")):
                os.makedirs(os.path.join(setup_directory,'.paa.tracking'))

            shutil.copy(drawio_filepath, os.path.join(
                setup_directory, ".paa.tracking",".drawio"))

            return True
        return False
