"""
Shouter

This class uses the logging module to create and manage a logger for displaying formatted messages.
It provides a method to output various types of lines and headers, with customizable message and line lengths.
The purpose is to be integrated into other classes that also use logger.
"""


import logging
import attr #>=22.2.0


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
    # Formating types

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

    def _format_mess(self,
                     mess : str,
                     dotline_length : int,
                     output_type : str,
                     method : str):

        """
        Format message before it is passed to be displayed.
        """

        switch = {
            "default" : lambda : mess,
            "dline": lambda: "=" * dotline_length,
            "line": lambda: "-" * dotline_length,
            "pline": lambda: "." * dotline_length,
            "HEAD1": lambda: "".join(["\n",
                                        "=" * dotline_length,
                                        "\n",
                                        "-" * ((dotline_length - len(mess)) // 2 - 1),
                                        mess,
                                        "-" * ((dotline_length - len(mess)) // 2 - 1),
                                        " \n",
                                        "=" * dotline_length]),
            "HEAD2": lambda: "".join(["\n",
                                        "*" * ((dotline_length - len(mess)) // 2 - 1),
                                        mess,
                                        "*" * ((dotline_length - len(mess)) // 2 - 1)]),
            "HEAD3": lambda: "".join(["\n",
                                        "/" * ((dotline_length - 10 - len(mess)) // 2 - 1),
                                        mess,
                                        "\\" * ((dotline_length - 10 - len(mess)) // 2 - 1)]),
            "title": lambda: f"** {mess}",
            "subtitle": lambda: f"*** {mess}",
            "subtitle2": lambda: f"+++ {mess}",
            "subtitle3": lambda: f"++++ {mess}",
            "warning": lambda: f"!!! {mess} !!!",
        }

        output_type = self._select_output_type(mess = mess,
                                               output_type = output_type)

        return switch[output_type]()


    def _select_output_type(self,
                              mess : str,
                              output_type : str):

        """
        Based on message and some other information, select output_type.
        """


        if output_type is None:

            if mess is not None:
                output_type = 'default'
            else:
                output_type = 'dline'

        return output_type



    def info(self,
             mess : str = None,
             dotline_length : int = None,
             output_type : str = None,
             logger : logging.Logger = None) -> None:

        """
        Prints info message similar to standard logger but with types of output and some additional actions.
        """


        if dotline_length is None:
            dotline_length = self.dotline_length

        if logger is None:
            logger = self.logger


        logger.info(self._format_mess(mess = mess,
                                      dotline_length = dotline_length,
                                      output_type = output_type,
                                      method = 'info'))

    def debug(self,
             mess : str = None,
             dotline_length : int = None,
             output_type : str = None,
             logger : logging.Logger = None) -> None:

        """
        Prints debug message similar to standard logger but with types of output and some additional actions.
        """


        if dotline_length is None:
            dotline_length = self.dotline_length

        if logger is None:
            logger = self.logger


        logger.debug(self._format_mess(mess = mess,
                                      dotline_length = dotline_length,
                                      output_type = output_type,
                                      method = 'debug'))

    def warning(self,
             mess : str = None,
             dotline_length : int = None,
             output_type : str = None,
             logger : logging.Logger = None) -> None:

        """
        Prints warning message similar to standard logger but with types of output and some additional actions.
        """


        if dotline_length is None:
            dotline_length = self.dotline_length

        if logger is None:
            logger = self.logger


        logger.warning(self._format_mess(mess = mess,
                                      dotline_length = dotline_length,
                                      output_type = output_type,
                                      method = 'warning'))

    def error(self,
             mess : str = None,
             dotline_length : int = None,
             output_type : str = None,
             logger : logging.Logger = None) -> None:

        """
        Prints error message similar to standard logger but with types of output and some additional actions.
        """


        if dotline_length is None:
            dotline_length = self.dotline_length

        if logger is None:
            logger = self.logger


        logger.error(self._format_mess(mess = mess,
                                      dotline_length = dotline_length,
                                      output_type = output_type,
                                      method = 'error'))

    def fatal(self,
             mess : str = None,
             dotline_length : int = None,
             output_type : str = None,
             logger : logging.Logger = None) -> None:

        """
        Prints fatal message similar to standard logger but with types of output and some additional actions.
        """


        if dotline_length is None:
            dotline_length = self.dotline_length

        if logger is None:
            logger = self.logger


        logger.fatal(self._format_mess(mess = mess,
                                      dotline_length = dotline_length,
                                      output_type = output_type,
                                      method = 'fatal'))

    def critical(self,
             mess : str = None,
             dotline_length : int = None,
             output_type : str = None,
             logger : logging.Logger = None) -> None:

        """
        Prints critical message similar to standard logger but with types of output and some additional actions.
        """


        if dotline_length is None:
            dotline_length = self.dotline_length

        if logger is None:
            logger = self.logger


        logger.critical(self._format_mess(mess = mess,
                                      dotline_length = dotline_length,
                                      output_type = output_type,
                                      method = 'critical'))
