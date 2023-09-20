"""
Logger class for creating and managing process logs.
"""

import logging
import os
from typing import Any

from .file_handler import FileHandler


class Logger:
    '''
    #### Logger class for creating and managing process logs.

    #### Parameters:
    @param `name` (str): The name of the logger.

    @param `log_filepath` (str): The name or path of the log file to log messages into. It can be a relative or absolute path.
    If the file does not exist, it will be created.

    #### Attributes:
    @attr `_base_level` (logging.LEVEL): The base level for logging message.

    @attr `_format` (str): log message format.

    @attr `date_format` (str): Log date format string.

    @attr `file_mode` (str): Log file write mode.

    @attr `to_console` (str): Set to True if messages should also be logged on the terminal/console
    
    '''
    _base_level = logging.NOTSET
    _format: str = "%(asctime)s - %(levelname)s - %(message)s"
    date_format: str = "%d/%m/%Y %H:%M:%S (%Z)"
    file_mode: str = 'a+'
    to_console: bool = False

    def __init__(self, name: str, log_filepath: str) -> None:
        log_filepath = log_filepath.replace('/', '\\')
        if '\\' in log_filepath:
            os.makedirs(os.path.dirname(log_filepath), exist_ok=True)
        log_filepath = os.path.abspath(log_filepath)

        _, ext = os.path.splitext(log_filepath)
        if ext and ext != '.log':
            raise ValueError('Invalid extension type for log file')
        if not ext:
            log_filepath = f"{log_filepath}.log"
        self.filename = log_filepath
        self._logger = logging.getLogger(name)


    def __str__(self) -> str:
        if self._logger.name:
            return self._logger.name
        return super().__str__()
    
    def __setattr__(self, __name: str, __value: Any) -> None:
        super().__setattr__(__name, __value)
        self._update_config()

    
    def _to_console(self) -> None:
        '''
        Logs messages to the console.

        If `self.to_console` is True, all subsequent log messages will be logged to the console.
        '''
        # set up logging to console
        console = logging.StreamHandler()
        console.setLevel(self._base_level)
        # set a format which is simpler for console use
        formatter = logging.Formatter(fmt=self._format, datefmt=self.date_format.replace('(%Z)', '(%z)'))
        console.setFormatter(formatter)
        # add the handler to the logger object and remove any existing handlers
        handlers = self._logger.handlers
        for h in handlers:
            self._logger.removeHandler(h)
        self._logger.addHandler(console)


    def _update_config(self) -> None:
        '''Updates the logger's configuration.'''
        logging.basicConfig(filename=self.filename, level=self._base_level, 
                            format=self._format, datefmt=self.date_format,
                            filemode=self.file_mode, force=True)
        if self.to_console:
            try:
                self._to_console()
            except Exception as e:
                self.log_error(e)
        return None


    def set_base_level(self, level: str) -> None:
        '''
        Sets the base logging level for the logger.

        Args:
            - level (str): The logging level to set the logger to.
        '''
        if level.upper() == "INFO":
            self._base_level = logging.INFO
        elif level.upper() == "DEBUG":
            self._base_level = logging.DEBUG
        elif level.upper() == "WARNING":
            self._base_level = logging.WARNING
        elif level.upper() == "ERROR":
            self._base_level = logging.ERROR
        elif level.upper() == "CRITICAL":
            self._base_level = logging.CRITICAL
        else:
            raise ValueError(f'{level} is not a valid base logging level')
        return None

    
    def log(self, message: str | object, level: str | None = None):
        '''
        Logs a message to a file using the specified level. If no level is provided, the default level is INFO.

        Args:
            message (str): The message to log
            level (str, optional): The level to log the message with. Defaults to "INFO".    
        '''
        if level:
            try:
                return getattr(self, f"log_{level.lower()}")(message)
            except AttributeError:
                pass
        return self.log_info(message)


    def clear_logs(self):
        """Deletes all log messages in log file."""
        return FileHandler(self.filename).clear_file()


    def copy_log(self, destination: str):
        """
        Copies the log file to a specified destination.

        Args:
            destination (str): The path to the directory to copy the log file to.
        """
        return FileHandler(self.filename).copy_to(destination)


    def log_info(self, message: str  | object) -> None:
        '''Logs a message to a file using the INFO level'''
        self._logger.info(msg=message)
    

    def log_debug(self, message: str  | object) -> None:
        '''Logs a message to a file using the DEBUG level'''
        self._logger.debug(msg=message)
    

    def log_error(self, message: str  | object) -> None:
        '''Logs a message to a file using the ERROR level'''
        self._logger.error(msg=message)


    def log_warning(self, message: str  | object) -> None:
        '''Logs a message to a file using the WARNING level'''
        self._logger.warning(msg=message)

    
    def log_critical(self, message: str  | object) -> None:
        '''Logs a message to a file using the CRITICAL level'''
        self._logger.critical(msg=message)
        

