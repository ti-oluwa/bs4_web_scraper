"""
DESCRIPTION: ::
    This module contains the BS4BaseScraper class which is the base class for creating scraper subclasses.
"""

from typing import IO, Any, Dict, List
import requests
import os
import random
import time
import json
import math
from bs4 import BeautifulSoup, ResultSet
from bs4.element import Tag
from urllib3.util.url import parse_url, Url
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor

from . import utils
from . import translate
from .logging import Logger
from .exceptions import (InvalidURLError, UnsupportedLanguageError, FileError, InvalidScrapableTagError)
from .request_limiter import RequestLimitSetting
from .file_handler import FileHandler


# SCRAPE SITES WITH PAGINATION
class BS4BaseScraper:
    """
    #### Base web scraper class

    Avoid instantiating this class directly. Instead, create a subclass of this class and override the `scrape` method.

    #### Creating a subclass::
    >>> class BS4Scraper(BS4BaseScraper):
            def scrape(*args, **kwargs):
                # You can add custom code here
                return super()._scrape(*arg, **kwargs)
            # create custom methods
            def custom_method(...):
                ...

    You can get an idea of what arguments and keyword arguments are expected by the `_scrape` function by doing:
    >>> help(super()._scrape)

    NOTE: On instantiation of the class, a new request session is created. This session is used to make all related requests.

    #### Parameters:
    @param str `parser`: HTML or HTML/XML parser for BeautifulSoup. Default is "lxml", "html.parser" is another suitable parser.

    Available parsers::
    For more on parsers read the BeautifulSoup documentation [here](https://www.crummy.com/software/BeautifulSoup/bs4/doc/#installing-a-parser)

    @param str `html_filename`: Default name used to save '*.html' files.

    @param int `no_of_requests_before_pause`: Defines the number of requests that can be made before a pause is taken.
    This should not exceed 50 to avoid high frequency requests. The upper limit is 100.
    This is implemented to regulate the request rate to websites in order to avoid hitting the website's server at very high rates
    which can either to lead to a 429 response code, Permission denied error or complete access block. Default is 20.

    @param int `scrape_session_pause_duration`: Number of second for which a pause is observed after the max request 
    count has been reached before a reset. Defaults to "auto" but the minimum pause duration allowed is 5 seconds. When set to "auto", 
    the scraper decides the suitable pause duration based on `no_of_requests_before_pause`.

    @param int `max_no_of_retries`: Maximum number of times a failed request will be retried before moving on.

    #### `no_of_requests_before_pause`, `scrape_session_pause_duration` and `max_no_of_retries` are used to instantiate a `RequestLimitSetting` for the class instance.

    @param str `base_storage_dir`: The directory where the folder containing scraped website will be stored. Defaults to 
    the current directory.

    @param str `storage_path`: Path where the base(index) HTML file will be saved with respect to the `base_storage_dir`.
    Defaults to directly inside the `base_storage_dir`.

    @param str `log_filepath`: Name or path (relative or absolute) of the file logs will be written into. Defaults to '<self.__class__.__name__.lower()>.log'.
    This can also be a path to an already existing log file. It is independent of self.base_storage_dir(can be saved somewhere outside the base directory)

    For instance:
    >>> bs4_scraper = BS4WebScraper(..., log_filepath="/<directory_path>/<filename>/")

    @param str `translation_engine`: The translation engine to use for translation. Case sensitive. Defaults to 'google'. This can be any of the supported translation engines.
    If the translation engine is not supported, the default translation engine will be used. See `translators` package for more information or do:

    To use a different translation engine, do:
    >>> bs4_scraper = BS4WebScraper(..., translation_engine='bing')

    #### Supported translation engines:
    To get a list of the supported translation engines do:
    >>> print(bs4_web_scraper.translation_engines)
    
    #### Attributes:
    @attr str `base_url`: The base url of the website being scraped. The base url is the url that will be used to construct the absolute url of all relative urls in a website.

    @attr int `level_reached`: The depth or number of levels successfully scraped.

    @attr int `__max_no_of_threads`: Maximum number of threads to use for scraping. Defaults to 10.

    @attr list[str] `_scrapable_tags`: A tuple of HTML element tags the web scraper is permitted to scrape. By default, the web scraper is permitted
    to scrape all supported HTML element tags.

    Default supported HTML5 element tags:
    To get these, do;
    >>> print(BS4WebScraper()._scrapable_tags)

    @attr RequestLimitSetting `request_limit_setting`: the RequestLimitSetting instance used by the class instance.
    
    @attr list[str] `url_query_params`: A list of all url query parameters encountered during scraping.

    @attr Session `session`: A requests.Session object used by the class instance to make requests.

    @attr dict `auth_credentials`: `self.session` login or authentication credentials.

    @attr bool `is_authenticated`: True if `self.session` is authenticated, otherwise, False.

    @attr Logger `logger`: `Logger` object for creating and writing logs.

    @attr str `_request_user_agent`: 'User-Agent' header used in requests.

    """

    _base_url: str = None
    _auth_url: str = None
    _auth_credentials: Dict[str, str] = None
    _is_authenticated: bool = False
    _level_reached: int = 0
    __max_no_of_threads: int = 10
    _session: requests.Session = requests.Session()
    _request_user_agent: str = None
    url_query_params: Dict = {}
    translator: translate.Translator = translate.Translator()
    translate_to: str | None = None
    logger: Logger = None
    _scrapable_tags = (
        'script', 'link|{"rel": "stylesheet"}', 'img', 'use', 'audio',
        'video', 'link|{"as": "font"}', 'link|{"rel": "shortcut"}', 'link|{"rel": "icon"}',
        'link|{"rel": "shortcut icon"}', 'link|{"rel": "apple-touch-icon"}',
        'link|{"type": "image/x-icon"}', 'link|{"type": "image/png"}',
        'link|{"type": "image/jpg"}', 'link|{"type": "image/jpeg"}',
        'link|{"type": "image/svg"}', 'link|{"type": "image/webp"}',
        'meta|{"content": "og:image"}',
    )
    _tc_: List = []

    def __init__(self, parser: str = 'lxml', html_filename: str = "index.html", 
                no_of_requests_before_pause: int = 20, scrape_session_pause_duration: int | float | Any = "auto",
                max_no_of_retries: int = 3, base_storage_dir: str = '.', storage_path: str = '', 
                log_filepath: str | None = None, translation_engine: str | None = 'default') -> None:
        """
        Initializes the web scraper instance.
        """
        if not html_filename.endswith('.html'):
            raise FileError('`html_filename` should take the format `<filename>.html`.')
        if scrape_session_pause_duration == 'auto':
            scrape_session_pause_duration = max(math.ceil(0.542 * no_of_requests_before_pause), 5)
        if translation_engine and (translation_engine != 'default' 
                                    and translation_engine not in translate.translation_engines):
            raise UnsupportedLanguageError("Unsupported translation engine")

        if log_filepath:
            self.logger = Logger(name=f"Logger for {self.__class__.__name__}", log_filepath=log_filepath)
            self.logger.set_base_level('INFO')
            self.logger.to_console = True

        if translation_engine != "default":
            self.translator.translation_engine = translation_engine
        self.translator.logger = self.logger
        self.parser = parser
        self.html_filename = html_filename
        self.max_no_of_retries = max_no_of_retries
        self.base_storage_dir = os.path.abspath(base_storage_dir)
        self.storage_path = storage_path
        self.request_limit_setting = RequestLimitSetting(no_of_requests_before_pause, scrape_session_pause_duration, self.max_no_of_retries, self.logger)


    @property
    def is_authenticated(self):
        return self._is_authenticated

    @property
    def level_reached(self):
        return self._level_reached

    @property
    def base_url(self):
        return self._base_url

    @property
    def auth_url(self):
        return self._auth_url

    @property
    def auth_credentials(self):
        return self._auth_credentials

    @property
    def session(self):
        return self._session


    def __setattr__(self, __name: str, __value: Any) -> None:
        if __name == "_level_reached":
            if __value < 0:
                raise ValueError(f"`{__name}` cannot be less than 0")
        elif __name == "__max_no_of_threads":
            if __value < 1:
                raise ValueError(f"`{__name}` cannot be less than 1")
            if __value > 10:
                raise ValueError(f"`{__name}` cannot be greater than 10")
        return super().__setattr__(__name, __value)


    def log(self, msg: str, level: str | None = None) -> None:
        """
        Logs a message using `self.logger` or prints it out if `self.logger` is None.

        Args:
            msg (str): The message to log
            level (str | None): The level of message to log.
        """
        if self.logger and isinstance(self.logger, Logger):
            level = level if level else 'INFO'
            return self.logger.log(msg, level)
        elif self.logger and not isinstance(self.logger, Logger):
            raise TypeError('Invalid type for `self.logger`. `self.logger` should be an instance of bs4_web_scraper.logging.Logger')
        return print(msg + '\n')


    def get_base_url(self, url: str) -> str:
        '''
        Returns a base url containing only the host, scheme and port

        Args:
            url (str): The url to be parsed. The url should be of the format `http://www.example.com:80/path/to/resource?query=string`,
            The base url will be `http://www.example.com:80`.
        '''
        url_obj = parse_url(url)
        if not (url_obj.host and url_obj.scheme):
            raise InvalidURLError("Invalid url! URL has no host and no scheme")

        new_url_obj = Url(scheme=url_obj.scheme, host=url_obj.host, port=url_obj.port)
        return new_url_obj.url


    def set_base_url(self, url: str) -> None:
        '''
        Sets the base url. The base url is the url that will be used to construct the absolute url of a relative url.

        Args:
            url (str): The url to be parsed. The url should be of the format `http://www.example.com:80/path/to/resource?query=string`,
            The base url will be `http://www.example.com:80`.
        '''
        self._base_url = self.get_base_url(url)

    
    def _validate_auth_credentials(self, credentials: Dict[str, str]) -> str:
        '''
        Validates the authentication credentials.

        Returns the authentication URL.

        Args:
            credentials (dict): A dictionary containing the authentication credentials.
        '''
        req_cr = (
            'auth_username_field', 'auth_password_field',
            'auth_username', 'auth_password', 'auth_url'
        )
        for cr in req_cr:
            if not credentials.get(cr, None):
                raise KeyError(f"`{cr}` not found in `credentials`")

        for key, value in credentials.items():
            if not isinstance(value, str):
                raise TypeError(f'Invalid type for `{key}`. `{key}` should be of type str')

        auth_url_obj = parse_url(credentials.get("auth_url"))
        if not (auth_url_obj.host and auth_url_obj.scheme):
            raise InvalidURLError("`auth_url` is not a valid URL")
     
        if parse_url(self.base_url).host not in auth_url_obj.host:
            raise InvalidURLError("`auth_url` might be invalid as it is not related to `self.base_url`. Please re-check credentials.")
        return auth_url_obj.url


    def set_auth_credentials(self, credentials: Dict[str, str]) -> None:
        '''
        Sets the instance's request authentication related attributes from user provided credentials.
        
        Args:
            credentials (Dict[str, str]): Authentication credentials
        '''
        if not self.base_url:
            raise AttributeError("`self.base_url` must be set.")

        self._auth_url = self._validate_auth_credentials(credentials)
        _credentials = {}
        _credentials[credentials['auth_username_field']] = credentials['auth_username']
        _credentials[credentials['auth_password_field']] = credentials['auth_password']
        self._auth_credentials = _credentials
        return None


    def _get_suitable_no_threads(self, item_count: int) -> int:
        '''
        Calculates the number of threads to use for the current scraping session based on the 
        `request_limit_setting.pause_duration` and `item_count`.

        Returns the number of threads to use.

        Args:
            item_count (int): The number of items to be threaded.
        '''
        if item_count <= 0:
            raise ValueError("`item_count` should be greater than 0")
                
        no_of_threads = self.request_limit_setting.pause_duration // (self.request_limit_setting.max_request_count_per_second // self.request_limit_setting.pause_duration)
        no_of_threads = math.floor(math.log10(item_count * no_of_threads))
        no_of_threads = min(no_of_threads, self.__max_no_of_threads)
        return no_of_threads if no_of_threads > 0 else 1


    def make_soup(self, markup: str | bytes | IO , **kwargs: Any) -> BeautifulSoup:
        """
        Instantiates a BeautifulSoup with the markup provided and self.parser.

        Returns a soup.

        Args::
            * markup (str | bytes | IO ): string, readable bytes or file containing markup.
        """
        if isinstance(markup, IO) and not markup.readable():
            raise FileError("file object provided for `markup` does not support read")
                
        return BeautifulSoup(markup, self.parser, **kwargs)

    
    def make_soup_from_url(self, url: str, **kwargs: Any):
        """
        Similar to `make_soup` but a url can be provided instead of markup. 
        The function will get the url's markup and make a BeautifulSoup with it.

        Returns BeautifulSoup if response from url is OK else returns None.

        Args::
            url (str): url from which soup will be created
        """
        response = self.get(url)
        if response:
            return self.make_soup(response.content, **kwargs)
        return None


    def _scrape(self, url: str, scrape_depth: int = 1, credentials: Dict[str, str] | None = None, translate_to: str | None = None) -> None:
        '''
        Main scraping method.
        
        NOTE:
        * This method is not meant to be called directly. Use the `scrape` method instead.
        * This method is not thread safe. It is not meant to be called by multiple threads.
        '''
        if translate_to:
            self.translate_to = translate_to
        if self.level_reached == 0:
            self._base_url = self.get_base_url(url)
        if credentials:
            self.set_auth_credentials(credentials)   

        # Scraping 'n' levels (for n >= 0)
        # Initially, Scrape base level -> 'n = 0'
        self.log(f'~~~SCRAPING BASE LEVEL~~~\n')
        response = self.get(url)
        if response is not None:
            index_file_hdl = self.save_to_file(self.html_filename, self.storage_path, content=response.content)
        else:
            raise Exception('Unexpected response: %s' % response)

        soup = self.get_associated_files_and_return_soup(index_file_hdl) # get all ('*js', '*.css', font files, ...) of first page
        self.save_to_file(self.html_filename, self.storage_path, content=soup.prettify(formatter='html5', encoding='utf-8'), translate=False)

        while scrape_depth > 0:
            # Start scraping at level 'n = n + 1'
            link_tags = soup.find_all('a') # get all links on the page
            self.log(f'~~~SCRAPING AT LEVEL {self.level_reached + 1}~~~\n')
            with ThreadPoolExecutor() as executor:
                no_of_threads = self._get_suitable_no_threads(len(link_tags))
                for link_tags_sub_list in utils.slice_iterable(link_tags, no_of_threads):
                    results = executor.map(lambda link_tag: self.get_link_tag(link_tag, True), link_tags_sub_list)
            
            # Finished scraping level 'n = n + 1'
            # Re-write html file from which the associated links and files were gotten with soup containing new attributes (link_href, script_src, image_src, href's etc.)
            self.log("UPDATING HTML FILE WITH UPDATED ELEMENT ATTRIBUTES\n")
            self.save_to_file(self.html_filename, self.storage_path, content=soup.prettify(formatter='html5', encoding='utf-8'), translate=False)
            scrape_depth -= 1 
            self._level_reached += 1  
        
            # If `scrape_depth` is still greater than zero, prepare data for scraping next level
            if scrape_depth > 0:
                results = filter(lambda result: isinstance(result, FileHandler) and all(result), results)
                for html_file_hdl in results:
                    html_file_hdl.open_file('r')
                    soup = self.make_soup(html_file_hdl.file)
                    self.storage_path = html_file_hdl.filepath
                    self.html_filename = html_file_hdl.filename
                    continue
        return None


    def scrape(self, url: str, scrape_depth: int = 1, credentials: Dict[str, str] | None=None, translate_to: str = None) -> None:
        """
        #### Wrapper function for the private `_scrape` function of the class.

        Scrapes the website provided in the url argument. 
        The scraped content is saved to the `self.storage_path` directory.

        Args::
        * `url` (str): The url of the website or webpage to be scraped.
        * `scrape_depth` (int, optional): The number of levels deep to scrape. Defaults to 1.
        * `credentials` (Dict[str, str], optional): Authentication or login details for website. Defaults to None.
        * `translate_to` (str, optional): Language code for the language scraped content will be translated to. The source language
        is automatically detected by `self.translator`. Defaults to None.
        """
        raise NotImplementedError("Oops! You forgot to implement this method. Your method should pass the required arguments to the `_scrape` method.")


    def get_request_headers(self) -> dict:
        '''Returns a suitable request header'''
        if self.auth_credentials:
            if not self._request_user_agent:
                user_agents = utils.generate_random_user_agents()
                random.shuffle(user_agents)
                self._request_user_agent = random.choice(user_agents)
        else:
            user_agents = utils.generate_random_user_agents()
            random.shuffle(user_agents)
            self._request_user_agent = random.choice(user_agents)
        
        headers = {
            'accept': '*/*',
            "Accept-Encoding": "gzip, deflate",
            'Accept-Language': 'en-US,en;q=0.9,it;q=0.8,es;q=0.7',
            'origin': self.base_url,
            'Host': parse_url(self.base_url).host,
            'referer': self.base_url,
            'User-Agent': self._request_user_agent,
            "Dnt": "1",
            "Sec-Fetch-Dest": "document", 
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none", 
            "Sec-Fetch-User": "?1", 
        }
        return headers


    def authenticate(self, credentials: Dict[str, str] | None = None) -> None:
        '''
        Authenticates the scraper to scrape websites that require authentication.

        Args:
        * `credentials` (Dict[str, str], optional): The authentication credentials. Defaults to None.
        '''
        if not credentials and not (self.auth_credentials or self.auth_url):
            raise Exception('`credentials` must be provided if `self.auth_credentials` or `self.auth_url` have not been set.')
        if credentials:
            self.set_auth_credentials(credentials)

        self.log(f'AUTHENTICATING AT... --> {self.auth_url}\n')
        resp = self.session.get(url=self.auth_url) 
        # get and set csrftoken
        self._auth_credentials['csrfmiddlewaretoken'] = resp.cookies.get('csrftoken')
        resp = self.session.post(url=self.auth_url, data=self.auth_credentials)
        self._is_authenticated = resp.ok

        if self.is_authenticated:
            self.log('AUTHENTICATED!!!\n')
        else:
            self.log('AUTHENTICATION FAILED!!!\n', level='ERROR')


    def get(self, url: str) -> requests.Response | None:  
        '''
        Makes a GET request to url given, authenticates requests and limits request rate based on limit setting if provided. 
        
        Returns response if status code is OK. Returns None if request is stale(failed even after multiple retries)

        Args:
        * `url` (str): url to make request to.
        '''  
        url_obj = parse_url(url)
        url = url_obj.url
        headers = self.get_request_headers()
        self._session.headers.update(headers)        

        # authenticate if credentials are already set
        if not self.is_authenticated and (self.auth_credentials and self.auth_url):
            self.authenticate()

        if self.request_limit_setting is None:
            self.log('GETTING --> %s \n' % url)
            response = self.session.get(url, headers=headers)
            resp_ok = self._handle_response(response)
            if resp_ok is False:
                return self.get(url)

        else:
            if self.request_limit_setting.can_make_requests is True:
                self.log('GETTING --> %s \n' % url)
                response = self.session.get(url)
                self.request_limit_setting.request_made()
                resp_ok = self._handle_response(response)

                if resp_ok is False:
                    time.sleep(self.request_limit_setting.pause_duration * 2)
                    return self.get(url)
                elif resp_ok is None:
                    return None
            else:
                time.sleep(self.request_limit_setting.pause_duration)
                return self.get(url)
        return response


    def _handle_response(self, response: requests.Response):
        """
        Returns True if response is OK else False. Returns None is request is stale - cannot be retried.

        Args::
        * `response` (requests.Response): request response.
        """
        if response.ok:
            self.log('SUCCESS: REQUEST OK \n')
            return True
        else:
            self.log(f"REQUEST GOT RESPONSE CODE -> {response.status_code} \n", level='error')
            if self.request_limit_setting:
                self.request_limit_setting.got_response_error()
                if response.status_code == 429:
                    if self.request_limit_setting.can_retry is True:
                        self.log('RETRYING... \n')
                        return False
                    else:
                        self.log("STALE REQUEST! MOVING ON >>> \n", level='warning')
                        self.request_limit_setting.reset_max_retry()
                return None    
        return False

    
    def translate_markup(self, markup: str | bytes) -> str | bytes:
        '''
        Translates the HTML markup given using the translator set for the scraper.

        Returns the translated markup.

        Args::
        * `markup` (str | bytes): The markup to translate.
        '''
        if not isinstance(markup, (str, bytes)):
            raise TypeError("Invalid type for `markup`")
        is_bytes = isinstance(markup, bytes)

        self.log('TRANSLATING markup...\n')
        soup = self.make_soup(markup)
        markup = self.translator.translate_soup(soup, self.translate_to).prettify(formatter="html5")
        # NOT FUNCTIONAL FOR NOW
        # markup = self.translator.translate_html(markup, target_lang=self.translator.target_language)
        self.log("markup TRANSLATED!\n")

        # re-encode the markup if the initial markup was in bytes
        if is_bytes:
            self.log('RE-ENCODING markup...\n')
            markup = markup.encode('utf-8')
        return markup
    

    def save_to_file(self, filename: str, storage_path: str, content: str | bytes, 
                        mode: str = "wb", encoding: str | None = 'utf-8', translate: bool = True):
        '''
        Saves content to file using the specified arguments. 
        Creates the file if it does not exist.
        
        Returns the FileHandler object.

        Args:
        * `filename` (str): Name of the file to be created.
        * `storage_path` (str): Path to the directory where the file will be created. 
        If the path is absolute it will be saved in the given path else it will be saved in `self.base_storage_dir`.
        * `content` (str | bytes): Content to be written into the file.
        * `mode` (str, optional): Mode to be used when creating the file. Defaults to "wb".
        * `encoding` (str | None, optional): Encoding to be used when creating the file. Defaults to 'utf-8'.
        * `translate` (bool, optional): Whether to translate the content to the encoding specified. Defaults to True.

        '''
        if mode in ['rb', 'r']:
            raise ValueError("`%s` is not an allowed mode. Allowed modes: 'w+', 'wb+', 'w', 'wb', 'a', ..." % mode)
        if 'b' in mode and isinstance(content, str):
            raise TypeError("`mode` specified is a byte mode. content provide is of type str not bytes")
        if not 'b' in mode and isinstance(content, bytes):
            raise TypeError("`mode` specified is a string mode. content provide is of type bytes not str")

        # Translate content if necessary
        if translate and (self.translate_to and filename.endswith('.html')):
            content = self.translate_markup(content)

        try:
            if os.path.isabs(storage_path):
                if os.path.isdir(storage_path):
                    file_path = f"{storage_path}\{filename}"
                else:
                    file_path = storage_path   
            else:
                file_path = f"{self.base_storage_dir}\{storage_path}\{filename}"
                
            file_hdl = FileHandler(file_path, encoding, exists_ok=True, allow_any=True)
            file_hdl.write_to_file(content, mode) # write_mode
            self.log(f"{'CREATED' if file_hdl.created_file else 'WROTE INTO'} FILE -> {file_path} \n")
            return file_hdl
        
        except Exception as e:
            self.log(e, level='error')
            pass
            

    def parse_storage_path_from_Url(self, url_obj: Url, remove_str: str | None = None) -> str:
        '''
        Returns a suitable storage path from a Url object.

        Args:
        * `url_obj` (Url): Url object to be parsed.
        * `remove_str` (str): string to be removed from the path. Defaults to None.
        '''
        url_path = url_obj.path or ''
        url_path = url_path.replace(remove_str, '') if remove_str else url_path
        return url_path.replace('/', '\\')


    def get_rra_by_tag_name(self, tag_name: str) -> str | None:
        '''
        Return the tag attribute that contains the src url/path.

        Returns None if tag name is not recognizable.

        Args:
        * `tag_name` (str): Tag name to be checked.
        
        '''
        tag_name = tag_name.lower()
        src = None
        if tag_name in ['audio', 'iframe', 'track', 'img', 'source', 'script', 'embed', 'video']:
            src = 'src'
        if tag_name in ['link', 'a', 'use']:
            src = 'href'
        return src
        

    def download_url(self, url: str, save_as: str | None = None, save_to: str | None = None, 
                        check_ext: bool = True, unique_if_query_params: bool = False):
        '''
        Download file from the given url. Saves the file in a storage path in `self.base_storage_dir`.

        Returns the FileHandler object for the downloaded file if downloaded or already existing else None.

        Args::
        * url (str): Url to be downloaded.
        * save_as Optional[str]: Name of the file to be downloaded or name with which the file should be saved.
        * save_to Optional[str]: Path to the directory where the file should be saved in `self.base_storage_dir`.
        * check_ext (bool, optional): Whether to check for extension in the url and use it for filename validation. Defaults to True.
        * unique_if_query_params (bool, optional): Whether to add a unique string to the filename if the url has query parameters. Defaults to False.
        
        #### NOTE::
        * If `save_as` is not provided, the filename will be extracted from the url.
        * If `save_to` is not provided, then `save_to` will automatically be the url path.
        * If the url you want to download from does not have an filename with extension, you should set `check_ext` to False and provide a value for `save_as`.
            
        An example of a url with a filename and extension is: https://example.com/style.css with 'style' as the name and '.css' as the extension.
        But a url like https://example.com/ does not have a filename with extension, you should provide a `save_as` name in this case, if not the 
        download may fail.

        * If the url already has a filename with extension, but you want to save the file with a different name, you can provide a value for `save_as` and set `check_ext` to False. 
            Just be careful as this may lead to saving files with no or incorrect file extensions.

        Example Usage::
            >>> bs4_scraper.download_url(url="https://example.com/", save_as="example.html", save_to="/examples", check_ext="False")
        '''
        url_obj = parse_url(url)
        if not url_obj.netloc:
            raise InvalidURLError
    
        url_based_name, url_based_ext = os.path.splitext((url_obj.path or '').split('/')[-1])
        if check_ext and not url_based_ext:
            raise ValueError('Invalid url. No extension found in url. The url may be incorrect.')
        filename = f"{url_based_name}{url_based_ext}"

        if save_as:
            if not isinstance(save_as, str):
                raise TypeError('`save_as` should be of type str')
            save_as_name, save_as_ext = os.path.splitext(save_as)
            if not (save_as_name and save_as_ext):
                raise ValueError('Invalid `save_as` name.')
            if check_ext and save_as_ext != url_based_ext:
                raise ValueError('Invalid extension! `save_as` extension does not match the extension in the url.')
            filename = f"{save_as_name}{save_as_ext}"

        if not filename:
            raise ValueError('`filename` seems to be empty. Please check the url "%s" or provide a `save_as` name.' % url)

        has_query_params = False
        response = None
        file_storage_path = save_to.replace('/', '\\').strip() if save_to is not None else save_to
        # check if element src has query params
        if url_obj.query:
            has_query_params = True
        if file_storage_path is None:
            file_storage_path = self.parse_storage_path_from_Url(url_obj, remove_str=f"{url_based_name}{url_based_ext}")
            # Clean up storage path
            file_storage_path = file_storage_path.replace(filename, '') if file_storage_path.endswith(f"{url_based_name}{url_based_ext}") else file_storage_path
            file_storage_path = file_storage_path[:-1] if file_storage_path.endswith('\\') else file_storage_path
            file_storage_path = file_storage_path[1:] if file_storage_path.startswith('\\') else file_storage_path        
                
        if has_query_params and (url_obj.query not in self.url_query_params.keys()):
            if unique_if_query_params is True:
                filename = utils.generate_unique_filename(filename)
                
        if has_query_params and (url_obj.query in self.url_query_params.keys()):
            file_hdl: FileHandler = self.url_query_params[url_obj.query]
            return file_hdl
            

        if not has_query_params or (url_obj.query not in self.url_query_params.keys()):
            # check if file already exists
            if os.path.exists(f'{self.base_storage_dir}\{file_storage_path}\{filename}') is False:
                response = self.get(url)
            else:
                self.log("`%s` ALREADY EXISTS! \n" % f'{self.base_storage_dir}\{file_storage_path}\{filename}')
                return FileHandler(f'{self.base_storage_dir}\{file_storage_path}\{filename}', exists_ok=True, allow_any=True)

        if response:
            downloaded_file_hdl = self.save_to_file(filename=filename, storage_path=file_storage_path, content=response.content)
            if downloaded_file_hdl:
                self.log("`%s` DOWNLOADED! \n" % url)
                if has_query_params:
                    self.url_query_params[url_obj.query] = downloaded_file_hdl 

            return downloaded_file_hdl
        return None


    def get_associated_files_and_return_soup(self, html_file_handler: FileHandler):
        '''
        Scrapes all the soup tags present in `self._scrapable_tags`
        
        Returns BeautifulSoup

        Args::
        * `html_file_handler` (FileHandler): HTML FileHandler object.
        '''
        if not isinstance(html_file_handler, FileHandler):
            raise TypeError("`html_file_handler` should be of type FileHandler")
        if html_file_handler.filetype not in ['html', 'xml']:
            raise FileError('Unsupported file type. File handled is not "html" or "xml".')

        html_file_handler.open_file('r')
        soup = self.make_soup(html_file_handler.file)
        tags = ResultSet(soup)
        for scrapable_tag in self._scrapable_tags:
            try:
                parts = scrapable_tag.split('|')
                if len(parts) == 1:
                    tag_name = scrapable_tag
                    tags.extend(soup.find_all(tag_name))
                elif len(parts) == 2:
                    tag_name = parts[0]
                    attrs = json.loads(parts[1])
                    tags.extend(soup.find_all(tag_name, attrs=attrs))

            except Exception:
                raise InvalidScrapableTagError(f"Invalid scrapable_tag, `{scrapable_tag}`, found in `self._scrapable_tags`")

        for tag in tags:
            rra_file_hdl = self.get_tag_rra(tag, download=True)
            # change the element's src to be compatible with the scraped website
            if isinstance(rra_file_hdl, FileHandler):
                # Find the relative path starting from the directory of the file from which the tag was gotten to the directory of the downloaded file
                src = self.get_rra_by_tag_name(tag.name)
                start_path = os.path.dirname(html_file_handler.filepath) if html_file_handler.filepath else f'{self.base_storage_dir}\\{self.storage_path}'
                dest_path = rra_file_hdl.filepath
                s_p = os.path.relpath(dest_path, start=start_path)
                s_p = s_p.replace('\\', '/')
                tag[src] = s_p if s_p.startswith('.') else f'./{s_p}'
            continue
        return soup


    def get_actual_url_from_rra(self, rra: str):
        '''
        Parses the url from a bs4.element.Tag rra

        Args::
        * `rra` (str): bs4.element.Tag resource-related-attribute
        '''
        url_obj = parse_url(rra)
        if url_obj.scheme and url_obj.netloc:
            actual_url = url_obj.url
        elif url_obj.netloc and not url_obj.scheme:
            actual_url = Url(
                scheme='http', host=url_obj.host, 
                path=url_obj.path, port= url_obj.port, 
                query=url_obj.query, auth=url_obj.auth,
                fragment=url_obj.fragment
            ).url
        else:
            actual_url = urljoin(self.base_url, url_obj.url)
        return actual_url


    def get_tag_rra(self, tag: Tag, download: bool = False):
        '''
        Gets the bs4.element.Tag object 'resource-related-attribute' if it has any.
        
        Returns the full resource URL if `download` is False or downloads the resource it points to if `download` is set to True.

        Returns None if it has no 'resource-related-attribute'

        A 'resource-related-attribute' in this case refers to any HTML tag attribute that points to a resource. Examples of
        resource-related-attributes include; 'href'(of the <link> tag) and 'src'(of the <img> tag).

        Args::
        * `tag` (Tag): tag with resource-related-attribute.
        * `download` (bool, optional): Whether to download the resource. Defaults to False.
        
        '''
        if not isinstance(tag, Tag):
            raise TypeError('`tag` should be of type bs4.tag.Tag')

        src = self.get_rra_by_tag_name(tag.name)
        tag_src = tag.get(src, None)
        if tag.name.lower() == 'use':
            tag_src = tag_src.split('#')[0]

        if tag_src:
            tag_src = tag_src.replace('..', '').replace('./', '/')
            if tag_src.startswith('//'):
                tag_src = tag_src.replace('//', '/')
            actual_url = self.get_actual_url_from_rra(tag_src)
            actual_url_obj = parse_url(actual_url)
            base_url_obj = parse_url(self.base_url)

            # Only scrape/download internal links, that is, links associated with the website being scraped only.
            if download and (base_url_obj.netloc and actual_url_obj.netloc) and (base_url_obj.netloc in actual_url_obj.netloc):
                file_hdl = self.download_url(url=actual_url, check_ext=False, unique_if_query_params=True)
                return file_hdl
            return actual_url_obj.url
        return None


    def get_link_tag(self, link_tag: Tag, download: bool = False):
        '''
        Get the link_tag href.
        
        Returns the downloaded page FileHandler if download is True else returns the page's URL.

        Returns None if it has no 'href'
        
        Args:
        * `link_tag` (Tag): bs4 'HTML <a></a>' Tag object.
        * `download` (bool, optional): Whether to download the page or file the link points to. Defaults to False.
        '''
        if not isinstance(link_tag, Tag):
            raise TypeError('`link_tag` should be of type Tag')
        if link_tag.name != 'a':
            raise ValueError('`link_tag` should be an HTML "a" tag')

        link_href = link_tag.get('href', None)
        if link_href:
            actual_url = self.get_actual_url_from_rra(link_href)
            actual_url_obj = parse_url(actual_url)
            base_url_obj = parse_url(self.base_url)

            # Only scrape internal links, that is, links associated with the website being scraped only.
            if download and (base_url_obj.netloc and actual_url_obj.netloc) and (base_url_obj.netloc in actual_url_obj.netloc):
                file_hdl = self.download_url(url=actual_url, save_as=self.html_filename, check_ext=False, unique_if_query_params=True)
                # change the link_tag's href to be compatible with the scraped website
                if file_hdl:
                    # Find the relative path starting from the directory of the html file/page from which the link tag was gotten 
                    # to the directory of the downloaded page
                    start_path = f'{self.base_storage_dir}\\{self.storage_path}'
                    dest_path = file_hdl.filepath
                    s_p = os.path.relpath(dest_path, start=start_path).replace('\\', '/')
                    link_tag['href'] = s_p
                    
                    new_soup = self.get_associated_files_and_return_soup(file_hdl)
                    # Re-write new_file with updated element attributes after all associated files have been gotten
                    self.log("UPDATING HTML FILE WITH UPDATED ELEMENT ATTRIBUTES\n")
                    file_hdl = self.save_to_file(self.html_filename, file_hdl.filepath, content=new_soup.prettify(formatter="html5", encoding='utf-8'), translate=False)
                    return file_hdl
            else:
                return actual_url_obj.url

        return None


