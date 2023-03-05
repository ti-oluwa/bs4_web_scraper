import logging, time, os


class Logger:
    _level = logging.INFO
    _format: str = "%(asctime)s - %(levelname)s - %(message)s"

    def __init__(self, log_filename: str):
        if not isinstance(log_filename, str):
            raise ValueError('Invalid argument type for `log_filename`')

        _, ext = os.path.splitext(log_filename)
        if ext and ext != '.log':
            raise ValueError('Invalid extension type for log file')
        if not ext:
            log_filename = f"{log_filename}.log"

        self.filename = log_filename

    def _update_basic_config(self):
        logging.basicConfig(filename=self.filename, level=self._level, 
                            format=self._format, datefmt="%H:%M:%S")
    
    def log(self, message: str, level: str | None="INFO"):
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

    def log_info(self, message: str):
        if not message:
            ValueError("`message` is a required argument")
        if not isinstance(message, str):
            ValueError("`message` should be of type str")
        
        self._level = logging.INFO
        self._update_basic_config()
        logging.info(msg=message)
    
    def log_debug(self, message: str):
        if not message:
            ValueError("`message` is a required argument")
        if not isinstance(message, str):
            ValueError("`message` should be of type str")

        self._level = logging.DEBUG
        self._update_basic_config()
        logging.debug(msg=message)
    
    def log_error(self, message: str):
        if not message:
            ValueError("`message` is a required argument")
        if not isinstance(message, str):
            ValueError("`message` should be of type str")
            
        self._level = logging.ERROR
        self._update_basic_config()
        logging.error(msg=message)

    def log_warning(self, message: str):
        if not message:
            ValueError("`message` is a required argument")
        if not isinstance(message, str):
            ValueError("`message` should be of type str")
            
        self._level = logging.WARNING
        self._update_basic_config()
        logging.warning(msg=message)
        



            
class RequestLimitSetting:
    '''
    #### BS4WebScraper requests limiting setting.

    @param int `request_count`: number of request that can be made before pausing requests.

    @param int `pause_duration`: number of seconds for which all requests will be paused before 
    allowing requests to be made again. Default is 3 seconds.

    @param int `max_retries`: maximum number of times a failed request will be retried before moving on.
    Default is 2 retries.

    @param Logger `logger`: `Logger` instance to be used to write logs.

    @attr bool `request_paused`: is True if requests are paused.

    @attr int `max_request_count_per_second`: returns the value provided for :param `request_count`.

    @attr int `no_of_available_retries`: Maximum number of times a failed request will be retried before moving on.

    @attr int `no_of_available_request`: Defines the number of requests that can be made before a pause is taken.

    @attr bool `can_make_requests`: is True if `request_paused` is False, otherwise, False.
    '''
    requests_paused = False
    logger: Logger = None
    
    def __init__(self, request_count: int, pause_duration: int | float = 3, max_retries: int = 2, logger: Logger = None):
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


    def request_made(self):
        '''Registers that a request has been made'''
        self.no_of_available_request -= 1
        if self.no_of_available_request == 0:
            self.pause()
            self.no_of_available_request = self.max_request_count_per_second
            self._log("NUMBER OF AVAILABLE REQUESTS RESET!\n")


    def _log(self, message: str):
        '''Logs a message using `self.logger` or prints it out if `self.logger` is None'''
        if self.logger:
            self.logger.log(message)
        else:
            print(message)            


    def got_response_error(self):
        '''Registers a request response error.'''
        self.no_of_available_retries -= 1

    def reset_max_retry(self):
        '''Resets the the maximum number of retries to the default provided value.'''
        self.no_of_available_retries = self.max_retries

    @property
    def can_make_requests(self):
        '''Returns if requests can be made, if self.request_paused is True, returns False'''
        return (not self.requests_paused)

    @property
    def can_retry(self):
        '''Returns True if the maximum number of retries has not been exceeded.'''
        return self.no_of_available_retries > 0

    def pause(self):
        '''Disallows request making for the specified pause duration.'''
        self.requests_paused = True
        self._log("REQUESTS PAUSED")
        self._log('-------------------')
        self._log("WAITING...")
        self._log('-------------------')
        time.sleep(self.pause_duration)
        self.requests_paused = False
        self._log("REQUESTS RESTARTED \n")


