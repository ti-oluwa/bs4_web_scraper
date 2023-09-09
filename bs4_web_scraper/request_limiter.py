import time
from typing import Any

from .logger import Logger



class RequestLimitSetting:
    '''
    #### Requests limiting setting.
    Regulates the frequency of requests

    #### Parameters:
    @param int `request_count`: number of request that can be made before pausing requests.

    @param int `pause_duration`: number of seconds for which all requests will be paused before 
    allowing requests to be made again. Default is 5 seconds.

    @param int `max_retries`: maximum number of times a failed request will be retried before moving on.
    Default is 3 retries.

    @param Logger `logger`: `Logger` instance to be used to write logs.

    #### Attributes:
    @attr bool `request_paused`: is True if requests are paused.

    @attr int `max_request_count_per_second`: returns the value provided for :param `request_count`. It should be within range
    1 - 100.

    @attr int `no_of_available_retries`: Maximum number of times a failed request will be retried before moving on.

    @attr int `no_of_available_request`: Defines the number of requests that can be made before a pause is taken.

    @attr bool `can_make_requests`: is True if `request_paused` is False, otherwise, False.
    '''
    requests_paused = False
    logger: Logger = None
    
    def __init__(
            self, 
            request_count: int, 
            pause_duration: int | float = 5, 
            max_retries: int = 2, 
            logger: Logger = None,
            log_to_console: bool = True
        ) -> None:
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
        self.log_to_console = log_to_console


    def __setattr__(self, __name: str, __value: Any) -> None:
        if __name == "pause_duration" and __value < 5:
            raise ValueError("`pause_duration` cannot be less than 5 seconds")
        if __name == "max_request_count_per_second" and (__value < 1 or __value > 100):
            raise ValueError("`max_request_count_per_second` cannot be less than 1 or greater than 100")
        return super().__setattr__(__name, __value)


    def request_made(self) -> None:
        '''Registers that a request has been made'''
        self.no_of_available_request -= 1
        if self.no_of_available_request == 0:
            self.pause()
            self.no_of_available_request = self.max_request_count_per_second
            self._log("NUMBER OF AVAILABLE REQUESTS RESET!\n")


    def _log(self, message: str, level: str | None = None) -> None:
        '''
        Logs a message using `self.logger` or prints it out if `self.logger` is None.

        Args:
            message (str): The message to log
            level (str | None): The level of message to log.
        '''  
        if self.logger and isinstance(self.logger, Logger):
            prev_val = self.logger.to_console 
            try:
                self.logger.to_console = self.log_to_console
                return self.logger.log(message, level)
            finally:
                self.logger.to_console = prev_val 
        elif self.logger and not isinstance(self.logger, Logger):
            raise TypeError('Invalid type for `self.logger`. `self.logger` should be an instance of bs4_web_scraper.logging.Logger')  
        if self.log_to_console:
            print(message + '\n') 
        return None    


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
        self._log('=================== \n')
        self._log("WAITING... \n")
        self._log('=================== \n')
        time.sleep(self.pause_duration)
        self.requests_paused = False
        self._log("REQUESTS RESTARTED \n")

