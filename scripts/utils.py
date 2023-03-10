"""
DESCRIPTION: ::
    Utility functions for the bs4_web_scraper package.
"""

import logging
import time
import os
import random
import string
from typing import List, Any


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
        raise ValueError('`old_filename` should be of type str')

    name, ext = os.path.splitext(old_filename)
    unique_filename = f"{name}{generate_unique_id()}{ext}"
    return unique_filename


def slice_list(_list: List, slice_size: int) -> list:
    '''
    Slices a list into smaller lists of size `slice_size`

    Args:
        _list (List): The list to slice
        slice_size (int): The size of each slice
    
    '''
    if not isinstance(_list, list):
        raise ValueError('Invalid argument type for `list`')
    if not isinstance(slice_size, int):
        raise ValueError('Invalid argument type for `slice_size`')
    if slice_size < 1:
        raise ValueError('`slice_size` should be greater than 0')

    return [_list[i:i+slice_size] for i in range(0, len(_list), slice_size)]


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
    Logger class for logging messages to a file.

    Parameters:
    -----------
    @param name (str): The name of the logger.

    @param log_filename (str): The name of the log file to log messages to.
    
    '''
    _base_level = logging.NOTSET
    _format: str = "%(asctime)s - %(levelname)s - %(message)s"
    date_format: str = "%d/%m/%Y %H:%M:%S (%Z)"
    file_mode: str = 'a'
    to_console: str = False

    def __init__(self, name: str, log_filename: str) -> None:
        if not isinstance(name, str):
            raise ValueError('Invalid argument type for `name`')
        if not isinstance(log_filename, str):
            raise ValueError('Invalid argument type for `log_filename`')

        _, ext = os.path.splitext(log_filename)
        if ext and ext != '.log':
            raise ValueError('Invalid extension type for log file')
        if not ext:
            log_filename = f"{log_filename}.log"
        self.filename = log_filename

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
            raise ValueError('`level` should be of type str')
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
            raise ValueError('`level` should be of type str')

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
            ValueError("`message` should be of type str")
        
        self._update_config()
        self._logger.info(msg=message)
    
    def log_debug(self, message: str) -> None:
        '''Logs a message to a file using the DEBUG level'''
        if not message:
            ValueError("`message` is a required argument")
        if not isinstance(message, str):
            ValueError("`message` should be of type str")

        self._update_config()
        self._logger.debug(msg=message)
    
    def log_error(self, message: str) -> None:
        '''Logs a message to a file using the ERROR level'''
        if not message:
            ValueError("`message` is a required argument")
        if not isinstance(message, str):
            ValueError("`message` should be of type str")
            
        self._update_config()
        self._logger.error(msg=message)

    def log_warning(self, message: str) -> None:
        '''Logs a message to a file using the WARNING level'''
        if not message:
            ValueError("`message` is a required argument")
        if not isinstance(message, str):
            ValueError("`message` should be of type str")
            
        self._update_config()
        self._logger.warning(msg=message)
    
    def log_critical(self, message: str) -> None:
        '''Logs a message to a file using the CRITICAL level'''
        if not message:
            ValueError("`message` is a required argument")
        if not isinstance(message, str):
            ValueError("`message` should be of type str")
            
        self._update_config()
        self._logger.critical(msg=message)
        



            
class RequestLimitSetting:
    '''
    #### BS4WebScraper requests limiting setting.

    Parameters:
    -----------
    @param int `request_count`: number of request that can be made before pausing requests.

    @param int `pause_duration`: number of seconds for which all requests will be paused before 
    allowing requests to be made again. Default is 5 seconds.

    @param int `max_retries`: maximum number of times a failed request will be retried before moving on.
    Default is 2 retries.

    @param Logger `logger`: `Logger` instance to be used to write logs.

    Attributes:
    -----------
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
            raise ValueError('`request_count` should be of type int')
        if not isinstance(max_retries, int):
            raise ValueError('`max_retries` should be of type int')
        if not isinstance(pause_duration, (int, float)):
            raise ValueError("Invalid type: %s for `pause_duration`" % type(pause_duration))
        if logger and not isinstance(logger, Logger):
            raise ValueError('Invalid type for `logger`')

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
            raise ValueError('Invalid type for `message`')
            
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


