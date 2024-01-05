"""
Shouter

This class uses the logging module to create and manage a logger for displaying formatted messages.
It provides a method to output various types of lines and headers, with customizable message and line lengths.
The purpose is to be integrated into other classes that also use logger.
"""


import logging
import attr #>=22.2.0
import sklearn


@attr.s
class Shouter:

    """
    A class for managing and displaying formatted log messages.

    This class uses the logging module to create and manage a logger
    for displaying formatted messages. It provides a method to output
    various types of lines and headers, with customizable message and
    line lengths.
    """

    # Formatting settings
    dotline_length = attr.ib(default=50)

    # Logger settings
    logger = attr.ib(default=None)
    logger_name = attr.ib(default='Shouter')
    loggerLvl = attr.ib(default=logging.DEBUG)
    logger_format = attr.ib(default='(%(asctime)s) : %(name)s : [%(levelname)s] : %(message)s')

    def __attrs_post_init__(self):
        self.initialize_logger()

    def initialize_logger(self):

        """
        Initialize a logger for the class instance based on
        the specified logging level and logger name.
        """

        if self.logger is None:
            logging.basicConfig(level=self.loggerLvl,format=self.logger_format)
            logger = logging.getLogger(self.logger_name)
            logger.setLevel(self.loggerLvl)

            self.logger = logger

    def shout(self,
              mess : str = None,
              dotline_length : int = None,
              output_type : str = None,
              logger : logging.Logger = None) -> None:
        """
        Prints a formatted line or message to the log with various styling options.

        This method allows for different types of message formatting in the log, such as
        dotted lines, solid lines, or various header styles. The method can be customized
        with a specific message, line length, and output type.

        Args:
            mess (str, optional):
                The text message to be included in the log. If not specified, only a line
                or header (based on output_type) will be printed. Defaults to None.
            dotline_length (int, optional):
                The length of the line to be printed. If not specified, the class attribute
                `dotline_length` is used. Defaults to None.
            output_type (str, optional):
                The type of formatting to be applied. Options include "dline" for a dotted line,
                "line" for a solid line, "pline" for a period-separated line, "HEAD1", "HEAD2",
                "HEAD3" for various header styles, "title", "subtitle", "subtitle2", "subtitle3",
                and "warning" for different emphasis styles. Defaults to "dline".
            logger (logging.Logger, optional):
                A specific logger instance to be used for logging. If not provided, the class's
                own logger instance is used. Defaults to None.

        Returns:
            None

        Examples:
            shouter_instance.shout("HEAD1", mess="Important Header", dotline_length=50)
            shouter_instance.shout(output_type="warning", mess="Caution!", dotline_length=30)
        """

        if output_type is None:

            if mess is not None:
                output_type = 'subtitle'
            else:
                output_type = 'dline'

        if dotline_length is None:
            dotline_length = self.dotline_length

        if logger is None:
            logger = self.logger


        switch = {
            "dline": lambda: logger.info("=" * dotline_length),
            "line": lambda: logger.debug("-" * dotline_length),
            "pline": lambda: logger.debug("." * dotline_length),
            "HEAD1": lambda: logger.info("".join(["\n",
                                                "=" * dotline_length,
                                                "\n",
                                                "-" * ((dotline_length - len(mess)) // 2 - 1),
                                                mess,
                                                "-" * ((dotline_length - len(mess)) // 2 - 1),
                                                " \n",
                                                "=" * dotline_length])),
            "HEAD2": lambda: logger.info("".join(["\n",
                                                "*" * ((dotline_length - len(mess)) // 2 - 1),
                                                mess,
                                                "*" * ((dotline_length - len(mess)) // 2 - 1)])),
            "HEAD3": lambda: logger.info("".join(["\n",
                                                "/" * ((dotline_length - 10 - len(mess)) // 2 - 1),
                                                mess,
                                                "\\" * ((dotline_length - 10 - len(mess)) // 2 - 1)])),
            "title": lambda: logger.info(f"** {mess}"),
            "subtitle": lambda: logger.info(f"*** {mess}"),
            "subtitle2": lambda: logger.debug(f"+++ {mess}"),
            "subtitle3": lambda: logger.debug(f"++++ {mess}"),
            "warning": lambda: logger.warning(f"!!! {mess} !!!"),
        }

        switch[output_type]()