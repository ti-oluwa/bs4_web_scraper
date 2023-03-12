"""
DESCRIPTION: ::
    Utility functions for the bs4_web_scraper package.
"""

import logging
import time
import os
import yaml
import toml
import json
import csv
import pickle
import random
import string
from typing import (IO, Dict, Iterable, List, Any, Tuple)


# DEFAULT USER-AGENTS THAT CAN BE USED IN PLACE OF THE RANDOM USER-AGENTS
USER_AGENTS = [
   "Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
   "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36 Edg/109.0.1518.78",
]


def generate_unique_id() -> str:
    '''Returns a random string of random length'''
    sample = list('0123456789' + string.ascii_lowercase)
    id = "".join(random.choices(sample, k=random.randint(4, 6)))
    return id


def generate_unique_filename(old_filename: str) -> str:
    '''
    Returns the old filename but with a random id to make it unique.

    Args:
        old_filename (str): Old filename to be modified.
    
    '''
    if not isinstance(old_filename, str):
        raise TypeError('`old_filename` should be of type str')

    name, ext = os.path.splitext(old_filename)
    unique_filename = f"{name}{generate_unique_id()}{ext}"
    return unique_filename


def slice_iterable(iterable: Iterable, slice_size: int) -> list[Iterable]:
    '''
    Slices an iterable into smaller iterables of size `slice_size`

    Args:
        iterable (Iterable): The iterable to slice.
        slice_size (int): The size of each slice
    
    '''
    if not isinstance(iterable, Iterable):
        raise TypeError('Invalid argument type for `iterable`')
    if not isinstance(slice_size, int):
        raise TypeError('Invalid argument type for `slice_size`')
    if slice_size < 1:
        raise ValueError('`slice_size` should be greater than 0')

    return [iterable[i:i+slice_size] for i in range(0, len(iterable), slice_size)]



def get_current_date() -> str:
    '''Returns the current date in the format: 12/12/2021'''
    return time.strftime("%d/%m/%Y", time.gmtime())


def get_current_date_time() -> str:
    '''Returns the current date and time in the format: 12/12/2021 12:12:12 (UTC)'''
    return time.strftime("%d/%m/%Y %H:%M:%S (%Z)", time.gmtime())


def get_current_time() -> str:
    '''Returns the current time in the format: 12:12:12 (UTC)'''
    return time.strftime("%H:%M:%S (%Z)", time.gmtime())


def generate_random_user_agents() -> list:
    '''Generates and returns three random and simple header user agents.'''
    nums = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

    random_agent1 = f"Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/{''.join(random.sample(nums, k=3))}.{''.join(random.sample(nums, k=1))}.{''.join(random.sample(nums, k=2))} (KHTML, like Gecko) Mobile/15E148"
    random_agent2 = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/10{''.join(random.sample(nums, k=1))}.{''.join(random.sample(nums, k=1))}.{''.join(random.sample(nums, k=1))}.{''.join(random.sample(nums, k=1))} Edg/10{''.join(random.sample(nums, k=1))}.{''.join(random.sample(nums, k=1))}.{''.join(random.sample(nums, k=4))}.{''.join(random.sample(nums, k=1))} Safari/537.36"
    random_agent3 = f"Mozilla/5.0 (Linux; Android 11; SAMSUNG SM-A207F) AppleWebKit/537.36 SamsungBrowser/19.0 (KHTML, like Gecko) Chrome/10{''.join(random.sample(nums, k=1))}.{''.join(random.sample(nums, k=1))}.{''.join(random.sample(nums, k=1))}.{''.join(random.sample(nums, k=1))} Safari/{''.join(random.sample(nums, k=3))}.{''.join(random.sample(nums, k=2))} Edg/10{''.join(random.sample(nums, k=1))}.{''.join(random.sample(nums, k=1))}.{''.join(random.sample(nums, k=4))}.{''.join(random.sample(nums, k=1))} Safari/537.36"
    
    user_agents = [
        random_agent1,
        random_agent2,
        random_agent3,
    ]
    return user_agents


class Logger:
    '''
    ### Logger class for logging messages to a file.

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
    to_console: str = False

    def __init__(self, name: str, log_filepath: str) -> None:
        if not isinstance(name, str):
            raise TypeError('Invalid argument type for `name`')
        if not isinstance(log_filepath, str):
            raise TypeError('Invalid argument type for `log_filepath`')

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
        try:
            self._to_console()
        except:
            pass


    def set_base_level(self, level: str) -> None:
        '''
        Sets the logging level for the logger.

        Args:
            - level (str): The logging level to set the logger to.
        '''
        if not isinstance(level, str):
            raise TypeError('`level` should be of type str')
        match level.upper():
            case "INFO":
                self._base_level = logging.INFO
            case "DEBUG":
                self._base_level = logging.DEBUG
            case "WARNING":
                self._base_level = logging.WARNING
            case "ERROR":
                self._base_level = logging.ERROR
            case "CRITICAL":
                self._base_level = logging.CRITICAL

    
    def log(self, message: str, level: str | None = "INFO") -> None:
        '''
        Logs a message to a file using the specified level. If no level is provided, the default level is INFO.

        Args:
            message (str): The message to log
            level (str, optional): The level to log the message with. Defaults to "INFO".    
        '''
        if level is None:
            return self.log_info(message)
        if not isinstance(level, str):
            raise TypeError('`level` should be of type str')

        match level.upper():
            case "INFO":
                return self.log_info(message)
            case "DEBUG":
                return self.log_debug(message)
            case "WARNING":
                return self.log_warning(message)
            case "ERROR":
                return self.log_error(message)
            case "CRITICAL":
                return self.log_critical(message)
        return self.log_info(message)


    def log_info(self, message: str) -> None:
        '''Logs a message to a file using the INFO level'''
        if not message:
            ValueError("`message` is a required argument")
        if not isinstance(message, str):
            TypeError("`message` should be of type str")
        
        self._logger.info(msg=message)
    
    def log_debug(self, message: str) -> None:
        '''Logs a message to a file using the DEBUG level'''
        if not message:
            ValueError("`message` is a required argument")
        if not isinstance(message, str):
            TypeError("`message` should be of type str")

        self._logger.debug(msg=message)
    
    def log_error(self, message: str) -> None:
        '''Logs a message to a file using the ERROR level'''
        if not message:
            ValueError("`message` is a required argument")
        if not isinstance(message, str):
            TypeError("`message` should be of type str")
            
        self._logger.error(msg=message)

    def log_warning(self, message: str) -> None:
        '''Logs a message to a file using the WARNING level'''
        if not message:
            ValueError("`message` is a required argument")
        if not isinstance(message, str):
            TypeError("`message` should be of type str")
            
        self._logger.warning(msg=message)
    
    def log_critical(self, message: str) -> None:
        '''Logs a message to a file using the CRITICAL level'''
        if not message:
            ValueError("`message` is a required argument")
        if not isinstance(message, str):
            TypeError("`message` should be of type str")
            
        self._logger.critical(msg=message)
        



            
class RequestLimitSetting:
    '''
    ### BS4WebScraper requests limiting setting.

    #### Parameters:
    @param int `request_count`: number of request that can be made before pausing requests.

    @param int `pause_duration`: number of seconds for which all requests will be paused before 
    allowing requests to be made again. Default is 5 seconds.

    @param int `max_retries`: maximum number of times a failed request will be retried before moving on.
    Default is 3 retries.

    @param Logger `logger`: `Logger` instance to be used to write logs.

    #### Attributes:
    @attr bool `request_paused`: is True if requests are paused.

    @attr int `max_request_count_per_second`: returns the value provided for :param `request_count`.

    @attr int `no_of_available_retries`: Maximum number of times a failed request will be retried before moving on.

    @attr int `no_of_available_request`: Defines the number of requests that can be made before a pause is taken.

    @attr bool `can_make_requests`: is True if `request_paused` is False, otherwise, False.
    '''
    requests_paused = False
    logger: Logger = None
    
    def __init__(self, request_count: int, pause_duration: int | float = 5, max_retries: int = 2, logger: Logger = None) -> None:
        if not isinstance(request_count, int):
            raise TypeError('`request_count` should be of type int')
        if not isinstance(max_retries, int):
            raise TypeError('`max_retries` should be of type int')
        if not isinstance(pause_duration, (int, float)):
            raise TypeError("Invalid type: %s for `pause_duration`" % type(pause_duration))
        if logger and not isinstance(logger, Logger):
            raise TypeError('Invalid type for `logger`')

        self.max_request_count_per_second = request_count
        self.pause_duration = pause_duration
        self.max_retries = max_retries
        self.no_of_available_request = request_count
        self.no_of_available_retries = max_retries
        self.logger = logger


    def __setattr__(self, __name: str, __value: Any) -> None:
        if __name == "pause_duration" and __value < 5:
            raise ValueError("`pause_duration` cannot be less than 5 seconds")
        if __name == "max_request_count_per_second" and __value == 0:
            raise ValueError("`max_request_count_per_second` cannot be 0")
        return super().__setattr__(__name, __value)

    def request_made(self) -> None:
        '''Registers that a request has been made'''
        self.no_of_available_request -= 1
        if self.no_of_available_request == 0:
            self.pause()
            self.no_of_available_request = self.max_request_count_per_second
            self._log("NUMBER OF AVAILABLE REQUESTS RESET!\n")


    def _log(self, message: str) -> None:
        '''
        Logs a message using `self.logger` or prints it out if `self.logger` is None.

        Args:
            message (str): The message to log
        '''
        if not isinstance(message, str):
            raise TypeError('Invalid type for `message`')
            
        if self.logger:
            self.logger.log(message)
        else:
            print(message)            


    def got_response_error(self) -> None:
        '''Registers a request response error.'''
        self.no_of_available_retries -= 1

    def reset_max_retry(self) -> None:
        '''Resets the the maximum number of retries to the default provided value.'''
        self.no_of_available_retries = self.max_retries

    @property
    def can_make_requests(self) -> bool:
        '''Returns if requests can be made, if self.request_paused is True, returns False'''
        return (not self.requests_paused)

    @property
    def can_retry(self) -> bool:
        '''Returns True if the maximum number of retries has not been exceeded.'''
        return self.no_of_available_retries > 0

    def pause(self) -> None:
        '''Disallows request making for the specified pause duration.'''
        self.requests_paused = True
        self._log("REQUESTS PAUSED \n")
        self._log('------------------- \n')
        self._log("WAITING... \n")
        self._log('------------------- \n')
        time.sleep(self.pause_duration)
        self.requests_paused = False
        self._log("REQUESTS RESTARTED \n")



class FileHandler:
    """
    ### Handles basic read and write operations on supported file types.

    #### Supported File Types:
    .csv, .json, .txt, .html, .xml, .yml, .yaml, .js, .css, .md, .toml
    .doc, .docx, .pdf, .pickle, .pkl. Mostly text based file types.

    #### Parameters:
    @param str `filepath`: path to the file to be read or written to.

    @param str `encoding`: encoding to be used when reading or writing to the file.

    @param bool `raise_not_found`: raise FileNotFoundError if file object specified by `filepath`
    cannot be found. If set to False, the file is created if it cannot be found. Defaults to False.

    #### Attributes:
    @attr str `filetype`: type of file to be read or written to. This is determined by the file extension.

    @attr IO `file`: file object to be read or written into.

    #### Methods:
    @method read_from_file: reads data from the file.

    @method write_to_file: writes data to the file.

    #### NOTE: All other methods are called based on the file type.
    """

    file: IO | None = None

    def __init__(self, filepath: str, encoding: str = 'utf-8', raise_not_found: bool = False) -> None:
        if not isinstance(filepath, str):
            raise TypeError("Invalid type for `filepath`")
        if not isinstance(encoding, str):
            raise TypeError("Invalid type for `encoding`")
        if not isinstance(raise_not_found, bool):
            raise TypeError("Invalid type for `raise_not_found`")
        
        self.filepath = os.path.abspath(filepath)
        if not os.path.exists(self.filepath):
            if raise_not_found:
                raise FileNotFoundError(f"File not found: {self.filepath}")
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        self.encoding = encoding
        # open file in append mode by default so it can be written into and read from 
        # even if the `_open_file` method has not being called yet.
        self._open_file('a+')


    @property
    def filetype(self) -> str:
        filetype = os.path.splitext(self.filepath)[-1].removeprefix('.').lower()
        if filetype in ['yaml', 'yml']:
            filetype = 'yaml'
        elif filetype in ['pickle', 'pkl']:
            filetype = 'pickle'
        return filetype

    @staticmethod
    def supported_file_types() -> List[str]:
        return [
        'txt', 'doc', 'docx', 'pdf', 'html', 'htm', 'xml',
         'js', 'css', 'md', 'json', 'csv', 'yaml', 'yml', 
         'toml', 'pickle', 'pkl',
        ]


    def _open_file(self, mode: str = 'a+') -> IO:
        '''
        Opens the file in the specified mode. Default mode is 'a+'.
        
        Args:
            mode (str): The mode to open the file in. Default is 'a+'
        '''
        try:
            self._close_file()
        except Exception:
            pass
        if 'b' in mode:
            self.file = open(self.filepath, mode=mode)
        else:
            self.file = open(self.filepath, mode=mode, encoding=self.encoding)
        return self.file

    def _close_file(self) -> None:
        '''
        Closes the file.
        '''
        self.file.close()
        return None

    def read_from_file(self, read_mode: str | None = None) -> Any:
        '''
        Reads the file and returns the content.

        Args:
            read_mode(str): The mode to be used to read the file. If None, it writes in read(r) mode.
        '''
        if read_mode and not isinstance(read_mode, str):
            raise TypeError("Invalid type for `read_mode`")
        if read_mode and read_mode not in ['r', 'rb', 'r+', 'rb+']:
            raise ValueError(f"Invalid literal `{read_mode}` for `read_mode`")

        if self.filetype in self.supported_file_types():
            self._open_file(read_mode or 'r+')
            try:
                return getattr(self, f'_read_{self.filetype}')()
            except:
                return self.file.read()
        raise Exception(F"Unsupported File Type: `{self.filetype}`")

    
    def write_to_file(self, content: Any, write_mode: str | None = None) -> None:
        '''
        Writes the content to the file.

        Args:
            content (Any): The content to write to the file.
            write_mode(str): The mode to be used to write the file. If None, it writes in append(a+) mode.
        '''
        if write_mode and not isinstance(write_mode, str):
            raise TypeError("Invalid type for `write_mode`")
        if write_mode and write_mode not in ['w', 'wb', 'w+', 'wb+', 'a+', 'a', 'ab+']:
            raise ValueError(f"Invalid literal `{write_mode}` for `write_mode`")

        if self.filetype in self.supported_file_types():
            self._open_file(write_mode or 'a+')
            try:
                return getattr(self, f'_write_{self.filetype}')(content)
            except:
                self.file.write(content)
                return None
        raise Exception(F"Unsupported File Type: `{self.filetype}`")
            

    def _read_json(self) -> Dict:
        '''
        Reads the file and returns the content as a dictionary.
        '''
        return json.load(self.file)


    def _write_json(self, content: dict, indent: int = 1) -> None:
        '''
        Writes the content to the file.

        Args:
            content (dict): The content to write to the file
        '''
        if not isinstance(content, dict):
            raise TypeError("Invalid type for `content`")
        _json = json.dumps(content, indent=indent)
        self.file.write(_json)
        return None


    def _write_csv(self, content: Iterable) -> None:
        '''
        Writes the content to the file.

        Args:
            content (list): The content to write to the file
        '''
        if not isinstance(content, Iterable):
            raise TypeError("Invalid type for `content`")
        writer = csv.writer(self.file)
        writer.writerows(content)
        return None


    def _read_csv(self) -> List:
        '''
        Reads the file and returns the content as a list.
        '''
        reader = csv.reader(self.file)
        return list(reader)


    def _read_yaml(self) -> Dict: #
        '''
        Reads the file and returns the content as a dictionary.
        '''
        return yaml.load(self.file, Loader=yaml.FullLoader)
    

    def _write_yaml(self, content: dict) -> None: #
        '''
        Writes the content to the file.

        Args:
            content (dict): The content to write to the file
        '''
        yaml.dump(content, self.file, default_flow_style=False)
        return None


    def _read_pickle(self) -> Any:
        '''
        Reads the file and returns the content.
        '''
        return pickle.load(self.file)


    def _write_pickle(self, content: Any) -> None:
        '''
        Writes the content to the file.

        Args:
            content (Any): The content to write to the file
        '''
        pickle.dump(content, self.file)
        return None


    def _read_toml(self) -> Dict:
        '''
        Reads the file and returns the content as a dictionary.
        '''
        return toml.load(self.file)


    def _write_toml(self, content: dict) -> None:
        '''
        Writes the content to the file.

        Args:
            content (dict): The content to write to the file
        '''
        toml.dump(content, self.file)
        return None


