"""
DESCRIPTION: ::
    This module contains the BS4WebScraper class which is the base class for creating scraper instances 
    used to scrape websites.

    Don't make high frequency requests! Scrape responsibly!
    If you are using this module to scrape websites for commercial purposes, please consider supporting the
    websites you are scraping by making a donation.
"""

from collections.abc import Iterable
from typing import Any, Dict, List
import requests
import os
import io
import random
import time
import json
import math
from bs4 import BeautifulSoup
from bs4.element import Tag, ResultSet
from urllib3.util.url import parse_url, Url
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor

from .utils import (Logger, RequestLimitSetting, FileHandler, slice_iterable,
                     generate_random_user_agents, generate_unique_filename)
from .help import available_translation_engines
from .translate import Translator


# SCRAPE SITES WITH PAGINATION
class BS4WebScraper:
    """
    ### BeautifulSoup4 web scraper class with support for authentication and translation.

    #### Instantiation and Example Usage: ::
        >>> bs4_scraper = BS4WebScraper(parser='lxml', html_filename='google.html',
                            no_of_requests_before_pause=50, scrape_session_pause_duration='auto',
                            base_storage_dir='./google', storage_path='/', 
                            log_filepath='google.log', ...)
        >>> bs4_scraper.scrape(url='https://www.google.com', scrape_depth=0)
            'google.html' saves to './google/google.html'
            A log file 'google.log' is created in the './google' directory


    #### NOTE: On instantiation of the class, a new request session is created. This session is used to make all related requests.

    Parameters:
    -----------
    @param str `parser`: HTML or HTML/XML parser for BeautifulSoup. Default is "lxml", "html.parser" is another suitable parser.

    #### Available parsers: ::
        - "lxml"
        - "lxml-xml"
        - "html.parser"
        - "html5lib"
         or it may be the type of markup to be used 
        - "html"
        - "html5"
        - "xml"
    
    For more on parsers read the BeatifulSoup documentation [here](https://www.crummy.com/software/BeautifulSoup/bs4/doc/#installing-a-parser)

    @param str `html_filename`: Default name used to save '*.html' files.

    @param int `no_of_requests_before_pause`: Defines the number of requests that can be made before a pause is taken.
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
    This can also be a path to an already existing log file.
    #### For instance:
    >>> bs4_scraper = BS4WebScraper(..., log_filepath="/<directory_path>/<filename>/")

    @param str `translation_engine`: The translation engine to use for translation. Case sensitive. Defaults to 'google'. This can be any of the supported translation engines.
    If the translation engine is not supported, the default translation engine will be used. See `translators` package for more information or do:

    >>> from bs4_web_scraper import help
    >>> print(help.available_translation_engines)

    #### To use a different translation engine, do:

    >>> bs4_scraper = BS4WebScraper(..., translation_engine='bing')

    #### Currently supported translation engines:
    - 'alibaba'
    - 'argos'
    - 'baidu'
    - 'bing'
    - 'caiyun'
    - 'deepl'
    - 'google'
    - 'iciba'
    - 'iflytek'
    - 'itranslate'
    - 'lingvanex'
    - 'niutrans'
    - 'mglip'
    - 'papago'
    - 'reverso'
    - 'sogou'
    - 'tencent'
    - 'translateCom'
    - 'utibet'
    - 'yandex'
    - 'youdao'

    Attributes:
    -----------
    @attr str `_base_url`: The base url of the website being scraped. The base url is the url that will be used to construct the absolute url of all relative urls in a website.

    @attr int `_level_reached`: The depth or number of levels successfully scraped.

    @attr int `max_no_of_threads`: Maximum number of threads to use for scraping. Defaults to 10.

    @attr list[str] `scrapable_tags`: A list of HTML element tags the web scraper is permitted to scrape. By default, the web scraper is permitted
    to scrape all supported HTML element tags.

    #### Currently supported HTML5 element tags:
    - `a`
    - `script`
    - `img`
    - `video`
    - `use`
    - `link|{"rel": "stylesheet"}`
    - `link|{"rel": "icon"}`
    - `link|{"rel": "shortcut"}`
    - `link|{"as": "font"}`
    - `link|{"rel": "apple-touch-icon"}`
    - `link|{"type": "image/x-icon"}` 
    - `link|{"type": "image/jpeg"}`
    - and a few others. . .

    @attr RequestLimitSetting `request_limit_setting`: the RequestLimitSetting instance used by the class instance.
    
    @attr list[str] `url_query_params`: A list of all url query parameters encountered during scraping.

    @attr Session `_request_session`: A requests.Session object used by the class instance to make requests.

    @attr str `_request_user_agent`: 'User-Agent' header used in requests.

    @attr dict `_auth_credentials`: `_request_session` login or authentication credentials.

    @attr bool `_is_authenticated`: True if `_request_session` is authenticated, otherwise, False.

    @attr Logger `logger`: `Logger` object for creating and writing logs.

    #
    """

    _base_url: str = None
    _auth_url: str = None
    _auth_credentials: Dict[str, str] = None
    _is_authenticated: bool = False
    _level_reached: int = 0
    max_no_of_threads: int = 10
    _request_session: requests.Session = requests.Session()
    _request_user_agent: str = None
    url_query_params: Dict = {}
    translator: Translator = Translator()
    scrapable_tags = [
        'script', 'link|{"rel": "stylesheet"}', 'img', 'use', 
        'video', 'link|{"as": "font"}', 'link|{"rel": "preload"}',
        'link|{"rel": "shortcut"}', 'link|{"rel": "icon"}',
        'link|{"rel": "shortcut icon"}', 'link|{"rel": "apple-touch-icon"}',
        'link|{"type": "image/x-icon"}', 'link|{"type": "image/png"}',
        'link|{"type": "image/jpg"}', 'link|{"type": "image/jpeg"}',
        'link|{"type": "image/svg"}', 'link|{"type": "image/webp"}',
    ]


    def __init__(self, parser: str = 'lxml', html_filename: str = "index.html", 
                no_of_requests_before_pause: int = 20, scrape_session_pause_duration: int | float | Any = "auto",
                max_no_of_retries: int = 3, base_storage_dir: str = '.', storage_path: str = '', 
                log_filepath: str | None = None, translation_engine: str | None = 'default') -> None:
        """
        Initializes the BS4WebScraper class instance.
        """
        try:
            soup = BeautifulSoup("<p>This is a test</p>", parser)
            soup.contents
        except Exception as e:
            raise ValueError(f"Invalid parser for BeautifulSoup: {parser}") from e
        if not isinstance(html_filename, str) or not html_filename.endswith('.html'):
            raise TypeError('`html_filename` should be of type str and should take the format `<filename>.html`.')
        if not isinstance(storage_path, str):
            raise TypeError('`storage_path` should be of type str')
        if not isinstance(base_storage_dir, str):
            raise TypeError('`base_storage_dir` should be of type str')
        if not isinstance(no_of_requests_before_pause, int):
            raise TypeError('`no_of_requests_before_pause` should be of type int')
        if not isinstance(scrape_session_pause_duration, (int, float, str)):
            raise TypeError('`scrape_session_pause_duration` should be of type int or float')
        if isinstance(scrape_session_pause_duration, str) and scrape_session_pause_duration != 'auto':
            raise TypeError('The only accepted string value for `scrape_session_pause_duration` is `auto`.')
        if scrape_session_pause_duration == 'auto':
            scrape_session_pause_duration = max(math.ceil(0.542 * no_of_requests_before_pause), 5)
        if log_filepath and not isinstance(log_filepath, str):
            raise TypeError('`log_filepath` should be of type str')

        if translation_engine and not isinstance(translation_engine, str):
            raise TypeError('`translation_engine` should be of type str')
        if translation_engine and (translation_engine != 'default' 
                                    and translation_engine not in available_translation_engines):
            raise Exception("Unsupported translation engine")

        
        if log_filepath:
            log_filepath.replace('/', '\\')
            if '\\' in log_filepath:
                os.makedirs(os.path.dirname(log_filepath), exist_ok=True)
            self.logger = Logger(name=f"Logger for {self.__class__.__name__}", log_filepath=log_filepath)
        else:
            self.logger = Logger(name=f"Logger for {self.__class__.__name__}", 
                                    log_filepath=self.__class__.__name__.lower())
        self.logger.set_base_level('INFO')
        self.logger.to_console = True

        if translation_engine != "default":
                self.translator.translation_engine = translation_engine
        
        self.translator.logger = self.logger
        self.parser = parser
        self.html_filename = html_filename
        self._base_html_filename = html_filename
        self.no_of_requests_before_pause = no_of_requests_before_pause
        self.scrape_session_pause_duration = scrape_session_pause_duration
        self.max_no_of_retries = max_no_of_retries
        base_storage_dir = base_storage_dir.replace('/', '\\')
        self.base_storage_dir = base_storage_dir
        self.storage_path = storage_path
        self.request_limit_setting = RequestLimitSetting(self.no_of_requests_before_pause, 
                                                            self.scrape_session_pause_duration, 
                                                            self.max_no_of_retries, self.logger)


    def __setattr__(self, __name: str, __value: Any) -> None:
        if __name == "_level_reached":
            if not isinstance(__value, int):
                raise TypeError(f"`{__name}` should be of type int")
            if __value < 0:
                raise ValueError(f"`{__name}` cannot be less than 0")
        elif __name == "max_no_of_threads":
            if not isinstance(__value, int):
                raise TypeError(f"`{__name}` should be of type int")
            if __value < 1:
                raise ValueError(f"`{__name}` cannot be less than 1")
            if __value > 10:
                raise ValueError(f"`{__name}` cannot be greater than 10")
        return super().__setattr__(__name, __value)


    def get_base_url(self, url: str) -> str:
        '''
        Returns a base url containing only the host, scheme and port

        Args:
            url (str): The url to be parsed. The url should be of the format `http://www.example.com:80/path/to/resource?query=string`,
            The base url will be `http://www.example.com:80`.
        '''
        if not isinstance(url, str):
            raise TypeError('`url` should be of type str')
        url_obj = parse_url(url)
        if not (url_obj.host and url_obj.scheme):
            raise ValueError('Invalid url!')

        new_url_obj = Url(scheme=url_obj.scheme, host=url_obj.host)
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
        if not isinstance(credentials, dict):
            raise TypeError('Invalid type for `credentials`')
        if len(credentials.items()) < 3:
            raise Exception('Some keys may be missing in `credentials`')
        if not credentials.get('auth_username_field', None):
            raise KeyError("`auth_username_field` not found in `credentials`")
        if not credentials.get('auth_password_field', None):
            raise KeyError("`auth_password_field` not found in `credentials`")
        if not credentials.get('auth_username', None):
            raise KeyError("`auth_username` not found in `credentials`")
        if not credentials.get('auth_password', None):
            raise KeyError("`auth_password` not found in `credentials`")
        if not credentials.get('auth_url', None):
            raise KeyError("`auth_url` not found in `credentials`")

        for key, value in credentials.items():
            if not isinstance(value, str):
                raise TypeError(f'Invalid type for `{key}`. `{key}` should be of type str')

        auth_url_obj = parse_url(credentials.get("auth_url"))
        if not (auth_url_obj.host and auth_url_obj.scheme):
            raise Exception("`auth_url` is not a valid URL")
     
        if parse_url(self._base_url).host not in auth_url_obj.host:
            raise Exception("`auth_url` might be invalid as it is not related to `self._base_url`. Please re-check credentials.")

        return auth_url_obj.url


    def set_auth_credentials(self, credentials: Dict[str, str]) -> None:
        '''
        Sets the instance's request authentication related attributes from user provided credentials.
        
        Args:
            credentials (Dict[str, str]): Authentication credentials
        '''
        if not self._base_url:
            raise AttributeError("`self._base_url` cannot be NoneType.")
        if not isinstance(self._base_url, str):
            raise AttributeError("Invalid type for `self._base_url`")
        if not isinstance(credentials, dict):
            raise TypeError('Invalid type for `credentials`')

        self._auth_url = self._validate_auth_credentials(credentials)
        _credentials = {}
        _credentials[credentials['auth_username_field']] = credentials['auth_username']
        _credentials[credentials['auth_password_field']] = credentials['auth_password']
        self._auth_credentials = _credentials


    def _get_suitable_no_threads(self, no_of_items: int) -> int:
        '''
        Calculates the number of threads to use for the current scraping session based on the 
        `request_limit_setting.pause_duration` and the no of items.

        Returns the number of threads to use.

        Args:
            no_of_items (int): The number of items to be scraped.
        '''
        try:
            no_of_items = int(no_of_items)
        except:
            raise ValueError("`no_of_items` should be of type int")
        if no_of_items <= 0:
            raise ValueError("`no_of_items` should be greater than 0")
                
        no_of_threads = self.request_limit_setting.pause_duration // (self.request_limit_setting.max_request_count_per_second // self.request_limit_setting.pause_duration)
        no_of_threads = math.floor(math.log10(no_of_items * no_of_threads))
        no_of_threads = min(no_of_threads, self.max_no_of_threads)
        return no_of_threads if no_of_threads > 0 else 1


    def _scrape(self, url: str, scrape_depth: int = 1, credentials: Dict[str, str] | None = None, translate_to: str | None = None) -> None:
        '''
        Main scraping method.
        
        NOTE: This method is not meant to be called directly. It is called by the `scrape` method.
        Use the `scrape` method instead.
        '''
        if not isinstance(url, str):
            raise TypeError('`url` should be of type str')

        _url_obj = parse_url(url)
        if not (_url_obj.host and _url_obj.scheme):
            raise ValueError('Invalid url! url should start with "http://" or "https://"')
        if not isinstance(scrape_depth, int):
            raise TypeError('`scrape_depth` should be of type int')

        # use proper url format
        url = _url_obj.url

        # set translator target lang
        if translate_to:
            self.translator.set_translator_target(translate_to)

        # set the base url of the website
        if self._level_reached == 0:
            self._base_url = self.get_base_url(url)
        if credentials:
            self.set_auth_credentials(credentials)
            
        links = None
        page_links_details = []

        # make initial request
        response = self._make_request(url)

        if response:
            # create file and get file content
            filename = self._base_html_filename
            name, ext = os.path.splitext((_url_obj.path or '').split('/')[-1])
            if ext and ext != '.html':
                filename = f'{name}{ext}'
            self.logger.log_info("BASE HTML FILE NAME: %s\n" % filename)

            if ext and ext == '.html':
                index_file = self._create_file(filename=filename, storage_path=self.storage_path, 
                                                content=response.text, create_mode='x', encoding='utf-8')
            else:
                index_file = self._create_file(filename=filename, storage_path=self.storage_path, content=response.content)
        else:
            raise Exception('Unexpected response type: %s' % type(response))

        file_content = index_file.read()
        # create soup
        soup = BeautifulSoup(file_content, self.parser)
        index_file.close()
        # get all associated files ('*js', '*.css', font files, ...)
        self._get_associated_files(soup)

        if scrape_depth > 0:
            links = soup.find_all('a')

        # get links
        if links:
            self.logger.log_error(f"NO OF LINKS: {len(links)}")
            self.logger.log_info(f'~~~SCRAPING AT LEVEL {self._level_reached + 1}~~~\n')
            with ThreadPoolExecutor() as executor:
                no_of_threads = self._get_suitable_no_threads(len(links))
                self.logger.log_error(f'NO OF THREADS: {no_of_threads}')
                for link_list in slice_iterable(links, no_of_threads):
                    values = executor.map(self._get_soup_link, link_list)
                    page_links_details.extend(values)
            # for link in links:
            #     page_link_detail = self._get_soup_link(link)
            #     page_links_details.append(page_link_detail)

            if self._level_reached == 0:
                self._level_reached += 1  

        # Create new base file with updated link_href, script_src, image_src, href's etc.
        self.logger.log_info("REWRITING BASE HTML FILE WITH UPDATED ELEMENT ATTRIBUTES\n")
        self._create_file(filename=self._base_html_filename, storage_path=self.storage_path, 
                            content=soup.prettify(), create_mode='w', 
                            encoding='utf-8', translate=False)
   
        scrape_depth -= 1
        if scrape_depth > 0:
            self.logger.log_info(f'~~~SCRAPING AT LEVEL {self._level_reached + 1}~~~\n')
            self._level_reached += 1

            for (url, storage_path, html_filename) in page_links_details:
                if all((url, storage_path, html_filename)):
                    self.storage_path = storage_path
                    self._base_html_filename = html_filename
                    return self._scrape(url, scrape_depth)


    def scrape(self, url: str, scrape_depth: int = 1, credentials: Dict[str, str] | None=None, translate_to: str = None) -> None:
        """
        #### Wrapper function for the private `_scrape` function.

        Scrapes the website provided in the url argument. 
        The scraped content is saved to the `self.storage_path` directory.

        Args: ::
            url (str): The url of the website or webpage to be scraped.
            scrape_depth (int, optional): The number of levels deep to scrape. Defaults to 1.
            credentials (Dict[str, str], optional): Authentication or login details for website. Defaults to None.
            translate_to (str, optional): Language code for the language scraped content will be translated to. The source language
            is automatically detected by `self.translator`. Defaults to None.

        #### AUTHENTICATION
        To scrape websites that require authentication. pass in the authentication credentials as an argument to the function.
        #### NOTE: credentials should take the format
        >>> credentials = {
            'auth_url': '<authentication_url>',
            'auth_username_field': '<username_field_name>',
            'auth_password_field': '<password_field_name>',
            'auth_username': '<username>',
            'auth_password': '<password>',
        }
        bs4_scraper = BS4WebScraper(...)
        bs4_scraper.scrape(..., credentials=credentials)


        #### TRANSLATION
        To translate scraped content to a specific language, the `translate_to` argument has to be provided. 
        To get a dict of the supported languages. do:
        
        >>> bs4_scraper = BS4WebScraper(...)
        >>> print(bs4_scraper.translator.supported_languages)
        >>> # Output: {'af': 'afrikaans', 'sq': 'albanian', 'am': 'amharic', ...}

        Make sure to set the `translation_engine` argument to the engine you want to use for translation.

        For instance to translate to 'amharic', do:
        >>> bs4_scraper.scrape(..., translate_to="am")

        #### NOTE: The `translate_to` argument is case insensitive.

        #
        """
        if translate_to and not isinstance(translate_to, str):
            raise TypeError("Invalid type for `translate_to`. It should be a string")

        self.logger.log_info("STARTING SCRAPING ACTIVITY...\n")
        self.logger.log_info(f"SCRAPING DEPTH: {scrape_depth if scrape_depth > 0 else 'BASE LEVEL'}\n")
        if translate_to:
            self.logger.log_info(f"TRANSLATION ENGINE: {self.translator.translation_engine.upper()}\n")
            self.logger.log_info(f"TRANSLATING TO: {translate_to.upper()}\n")

        start_time = time.perf_counter()
        self._scrape(url=url, scrape_depth=scrape_depth, credentials=credentials, 
                    translate_to=translate_to)
        finish_time = time.perf_counter()
        time_taken = finish_time - start_time

        if self._level_reached > 0:
            self.logger.log_info(f"SCRAPED {self._level_reached} LEVEL{'S'[:self._level_reached^1]} SUCCESSFULLY! \n")
        else:
            self.logger.log_info("SCRAPED BASE LEVEL SUCCESSFULLY! \n")

        if time_taken >= 60:
            self.logger.log_info(f"SCRAPING COMPLETED IN {(time_taken/ 60):.2f} MINUTES\n")
        else:
            self.logger.log_info(f"SCRAPING COMPLETED IN {time_taken:.2f} SECONDS\n")


    def get_request_headers(self) -> dict:
        '''Returns a suitable request header'''
        if not isinstance(generate_random_user_agents(), list):
            raise TypeError("Invalid return type for `self.generate_random_user_agents`")

        if self._auth_credentials:
            if not self._request_user_agent:
                user_agents = generate_random_user_agents()
                random.shuffle(user_agents)
                self._request_user_agent = random.choice(user_agents)
        else:
            user_agents = generate_random_user_agents()
            random.shuffle(user_agents)
            self._request_user_agent = random.choice(user_agents)
        
        headers = {
            'accept': '*/*',
            "Accept-Encoding": "gzip, deflate",
            'Accept-Language': 'en-US,en;q=0.9,it;q=0.8,es;q=0.7',
            'origin': self._base_url,
            'Host': parse_url(self._base_url).host,
            'referer': self._base_url,
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
            credentials (Dict[str, str], optional): The authentication credentials. Defaults to None.
        '''
        if not credentials and not (self._auth_credentials or self._auth_url):
            raise Exception('`credentials` must be provided if `self._auth_credentials` or `self._auth_url` have not been set.')
        if credentials:
            self.set_auth_credentials(credentials)

        self.logger.log_info(f'AUTHENTICATING AT... --> {self._auth_url}\n')
        resp = self._request_session.get(url=self._auth_url) 
        # get and set csrftoken
        self._auth_credentials['csrfmiddlewaretoken'] = resp.cookies.get('csrftoken')
        resp = self._request_session.post(url=self._auth_url, data=self._auth_credentials)
        self._is_authenticated = resp.ok

        if self._is_authenticated:
            self.logger.log_info('AUTHENTICATED!!!\n')
        else:
            self.logger.log_error('AUTHENTICATION FAILED!!!\n')


    def _make_request(self, url: str) -> requests.Response | None:  
        '''
        Makes a GET request to url given, authenticates requests and limits request rate based on limit setting if provided. 
        
        Returns response if OK.
        Args:
            url (str): url to make request to
        '''  
        if not isinstance(url, str):
            raise TypeError('url is not a string')
        url_obj = parse_url(url)
        if not (url_obj.netloc or url_obj.scheme):
            raise ValueError("Invalid url!")

        headers = self.get_request_headers()
        if not isinstance(headers, dict):
            raise TypeError("Invalid return type for `self.get_request_headers`")
        self._request_session.headers.update(headers)        

        # authenticate if credentials are already set
        if not self._is_authenticated and (self._auth_credentials and self._auth_url):
            self.authenticate()

        if self.request_limit_setting is None:
            self.logger.log_info('GETTING --> %s \n' % url)
            response = self._request_session.get(url, headers=headers)
            if response.status_code != 200:
                self.logger.log_error(f"REQUEST GOT RESPONSE CODE -> {response.status_code} \n")
                return self._make_request(url)
            return response

        else:
            if self.request_limit_setting.can_make_requests == True:
                self.logger.log_info("NUMBER OF AVAILABLE REQUEST: %s\n" % str(self.request_limit_setting.no_of_available_request))
                self.logger.log_info('GETTING --> %s \n' % url)
                response = self._request_session.get(url)

                if response.status_code == 200:
                    self.logger.log_info('SUCCESS: REQUEST OK \n')
                    self.request_limit_setting.request_made()
                    return response
                else:
                    self.logger.log_warning(f"REQUEST GOT RESPONSE CODE -> {response.status_code} \n")
                    self.request_limit_setting.request_made()
                    if self.request_limit_setting.can_retry and response.status_code not in [403, 404]:
                        self.request_limit_setting.got_response_error()
                        self.logger.log_info('RETRYING... \n')
                        time.sleep(self.request_limit_setting.pause_duration * 5)
                        return self._make_request(url)

                    elif not self.request_limit_setting.can_retry:
                        self.logger.log_warning("MAXIMUM NUMBER OF RETRIES REACHED! MOVING ON >>> \n")
                        self.request_limit_setting.reset_max_retry()
            else:
                self.logger.log_info('RETRYING... \n')
                time.sleep(self.request_limit_setting.pause_duration)
                return self._make_request(url)
        return None

    
    def _translate_content(self, content: str | bytes) -> str | bytes:
        '''
        Translates the content given using the translator set for the scraper.

        Returns the translated content.

        Args:
            content (str | bytes): The content to translate.
        '''
        if not isinstance(content, (str, bytes)):
            raise TypeError("Invalid type for `content`")
        is_bytes = isinstance(content, bytes)

        self.logger.log_info('TRANSLATING CONTENT...\n')
        soup = BeautifulSoup(content, self.parser)
        with ThreadPoolExecutor() as executor:
            for list_item in slice_iterable(soup.findAll(self.translator._translatable_elements), 50):
                executor.map(self.translator.translate_soup_element, list_item)
                time.sleep(self.request_limit_setting.pause_duration)
        content = soup.prettify()
        # NOT FUNCTIONAL FOR NOW
        # content = self.translator.translate_html(content, target_lang=self.translator.target_language)
        self.logger.log_info("CONTENT TRANSLATED!\n")

        # re-encode the content if the initial content was in bytes
        if is_bytes:
            self.logger.log_info('RE-ENCODING CONTENT...\n')
            content = content.encode('utf-8')
        return content
    

    def _create_file(self, filename: str, storage_path: str, content: str | bytes, 
                        create_mode: str = "xb", encoding: str | None = None, translate: bool = True) -> io.TextIOWrapper | io.BufferedWriter:
        '''
        Creates file using given arguments and write content into file. 
        If the file exists, just write the content into the file. 
        
        Returns the file object opened in read mode.

        Args:
            filename (str): Name of the file to be created.
            storage_path (str): Path to the directory where the file will be created.
            content (str | bytes): Content to be written into the file.
            create_mode (str, optional): Mode to be used when creating the file. Defaults to "xb".
            encoding (str | None, optional): Encoding to be used when creating the file. Defaults to None.
            translate (bool, optional): Whether to translate the content to the encoding specified. Defaults to True.

        '''
        if not isinstance(filename, str):
            raise TypeError("Invalid argument type for `filename`")
        if not isinstance(storage_path, str):
            raise TypeError("Invalid argument type for `storage_path`")
        if not isinstance(create_mode, str):
            raise TypeError("Invalid argument type for `create_mode`")
        if not isinstance(content, (bytes, str)):
            raise TypeError('Argument `content` can only be bytes or str.')
        if not isinstance(encoding, str) and encoding is not None:
            raise TypeError('Argument `encoding` can only be NoneType or str.')
        if create_mode not in ['x', 'xb', 'w', 'wb']:
            raise ValueError("`%s` is not an allowed mode. Allowed modes: 'x', 'xb', 'w', 'wb'." % create_mode)
        if create_mode in ['xb', 'wb'] and isinstance(content, str):
            raise TypeError("`create_mode` specified is a byte mode. content provide is of type str not bytes")
        if create_mode in ['x', 'w'] and isinstance(content, bytes):
            raise TypeError("`create_mode` specified is a string mode. content provide is of type bytes not str")
        if create_mode in ["x", "w"] and encoding is None:
            raise TypeError("Encoding cannot be NoneType when `create_mode` is 'x'.")

        # Translate if necessary
        if translate and (self.translator.target_language and filename.endswith('.html')):
            content = self._translate_content(content)

        # Set the correct mode for reading and writing based on the create_mode
        write_mode, read_mode = ("wb", "rb") if create_mode.endswith('b') else ("w", "r")

        try:
            dir_path = f"{self.base_storage_dir}\{storage_path}"
            os.makedirs(dir_path, exist_ok=True)
            with open(f"{dir_path}\{filename}", create_mode, encoding=encoding) as f:
                if f.writable():
                    f.write(content)
                    self.logger.log_info(f"{'CREATED' if create_mode in ['xb', 'x'] else 'WROTE'} FILE -> {dir_path}\{filename} \n")
                    f.close()
                    file = open(f"{dir_path}\{filename}", read_mode, encoding=encoding)
                    return file
                else:
                    raise Exception('File does not support write')
        
        except FileExistsError:
            return self._create_file(filename, storage_path, content, write_mode, encoding)
            

    def _parse_storage_path(self, url_obj: Url, remove_str: str | None = None) -> str:
        '''
        Returns a suitable storage path from a Url.

        Args:
            url_obj (Url): Url object to be parsed.
        '''
        if not isinstance(url_obj, Url):
            raise TypeError('`url_obj` should be of type Url')
        if remove_str and not isinstance(remove_str, str):
            raise TypeError('`remove_str` should be of type str')

        url_path = url_obj.path or ''
        url_path = url_path.replace(remove_str, '') if remove_str else url_path
        return url_path.replace('/', '\\')


    def _get_element_src_by_tag_name(self, tag_name: str) -> str:
        '''
        Return the tag attribute that contains the src url/path.

        Args:
            tag_name (str): Tag name to be checked.
        
        '''
        if not isinstance(tag_name, str):
            raise TypeError('`tag_name` should be of type str')
        tag_name = tag_name.lower()

        if tag_name in ['audio', 'iframe', 'track', 'img', 'source', 'script', 'embed', 'video']:
            return 'src'
        if tag_name in ['link', 'a', 'use']:
            return 'href'
        

    def download_url(self, url: str, save_as: str | None = None, save_to: str | None = None, 
                        check_ext: bool = True, unique_if_query_params: bool = False):
        '''
        Download file from the given url. Saves the file in a storage path in `self.base_storage_dir`.

        Returns the storage path of the downloaded file.

        Args:
            - url (str): Url to be downloaded.
            - save_as Optional[str]: Name of the file to be downloaded or name with which the file should be saved.
            - save_to Optional[str]: Path to the directory where the file should be saved in `self.base_storage_dir`.
            - check_ext (bool, optional): Whether to check for extension in the url and use it for filename validation. Defaults to True.
            - unique_if_query_params (bool, optional): Whether to add a unique string to the filename if the url has query parameters. Defaults to False.
        
        #### NOTE: ::
            - #### If `save_as` is not provided, the filename will be extracted from the url.
            - #### If `save_to` is not provided, then `save_to` will automatically be the url path.
            - #### If the url you want to download from does not have an filename with extension, you should set `check_ext` to False and provide a value for `save_as`.
            
            An example of a url with a filename and extension is: https://example.com/style.css with 'style' as the name and '.css' as the extension.
            But a url like https://example.com/ does not have a filename with extension, you should provide a `save_as` name in this case, if not the 
            download may fail.

            - #### If the url already has a filename with extension, but you want to save the file with a different name, you can provide a value for `save_as` and set `check_ext` to False. 
            Just be careful as this may lead to saving files with no or incorrect file extensions.

        #### Example Usage: ::
            >>> bs4_scraper.download_url(url="https://example.com/", save_as="example.html", save_to="/examples", check_ext="False")
        ''' 
        if not isinstance(check_ext, bool):
            raise TypeError('`check_ext` should be of type bool')
        if save_to and not isinstance(save_to, str):
            raise TypeError('`save_to` should be of type str')
        if not isinstance(unique_if_query_params, bool):
            raise TypeError('`unique_if_query_params` should be of type bool')
        if not url:
            raise ValueError('`url` is required.')
        if not isinstance(url, str):
            raise TypeError('`url` should be of type str')
        url_obj = parse_url(url)
        if url_obj.scheme not in ['http', 'https']:
            raise ValueError('Only http and https urls are allowed.')
        if not url_obj.netloc:
            raise ValueError('Invalid url.')
    
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
            raise ValueError('`filename` seems to be empty. Please check the url or provide a `save_as` name.')

        has_query_params = False
        response = None
        downloaded_file = None
        save_to = save_to.replace('/', '\\').strip() if save_to else ''
        storage_path = save_to 
        # check if element src has query params
        if url_obj.query:
            has_query_params = True
        if not save_to:
            storage_path = self._parse_storage_path(url_obj, remove_str=f"{url_based_name}{url_based_ext}")
            # Clean up storage path
            storage_path = storage_path.replace(filename, '') if storage_path.endswith(f"{url_based_name}{url_based_ext}") else storage_path
            storage_path = storage_path[:-1] if storage_path.endswith('\\') else storage_path
            storage_path = storage_path[1:] if storage_path.startswith('\\') else storage_path        
                
        if has_query_params and (url_obj.query not in self.url_query_params.keys()):
            if unique_if_query_params is True:
                filename = generate_unique_filename(filename)
                
        elif has_query_params and (url_obj.query in self.url_query_params.keys()):
            s_path = self.url_query_params[url_obj.query]
            return s_path, downloaded_file, s_path.split('\\')[-1]
            
        s_path = f"{self.base_storage_dir}\{storage_path}\{filename}"

        if not has_query_params or (url_obj.query not in self.url_query_params.keys()):
            # check if file already exists
            if os.path.exists(s_path) is False:
                response = self._make_request(url)
            else:
                self.logger.log_info("`%s` ALREADY EXISTS! \n" % s_path)

        if response:
            downloaded_file = self._create_file(filename=filename, storage_path=storage_path, content=response.content)
            if downloaded_file:
                self.logger.log_info("`%s` DOWNLOADED! \n" % url)
                if has_query_params:
                    self.url_query_params[url_obj.query] = s_path  

        return s_path, downloaded_file, filename
        

    def download_urls(self, urls: Iterable[Dict[str, str]], save_to: str | None = None, 
                        check_ext: bool = True, fast_download: bool = False, unique_if_query_params: bool = False):
        '''
        Download files from the given urls using the `download_url` method. Saves the files in a storage path in `self.base_storage_dir`.

        Returns the storage path of the downloaded files.

        Args:
            - urls (List[Dict[str, str]]): List of urls to be downloaded. The url in the list should be of type dict[str, str].
            - save_to Optional[str]: Path to the directory where the file should be saved in `self.base_storage_dir`.
            - check_ext (bool, optional): Whether to check for extension in the url and use it for filename validation. Defaults to True.
            Check the doc string of `download_url` for more info on setting this value.
            - unique_if_query_params (bool, optional): Whether to generate a unique filename if the any of the urls has query params. Defaults to False.
            - fast_download (bool, optional): Whether to download the urls in parallel. Defaults to False. 
            If the number or urls exceed 200 then fast download wont be used to avoid sending high frequency requests to the server.

        #### Example Usage: ::
            >>> urls = [
                    {'url': 'https://www.example.com/', 'save_as': 'site.html'},
                    {'url': 'https://www.example.com/image2.jpg', 'save_as': ''},
                    {'url': 'https://www.example.com/image3.jpg', 'save_as': 'image3.jpg'},
                ]
            >>> bs4_scraper.download_urls(urls=urls, save_to='images', fast_download=True)
        ''' 
        if not urls:
            raise ValueError('`urls` is required.')
        if not isinstance(urls, Iterable):
            raise TypeError('`urls` should be of type Iterable[dict[str, str]]')
        if not isinstance(unique_if_query_params, bool):
            raise TypeError('`unique_if_query_params` should be of type bool')
        if not isinstance(fast_download, bool):
            raise TypeError('`fast_download` should be of type bool')

        urls = list(filter(lambda url: isinstance(url, dict) and any(url), urls))

        if len(urls) < 1:
            raise ValueError("No valid url was found in `urls`")

        results = []
        params = {'save_to': save_to, 'check_ext': check_ext, 'unique_if_query_params': unique_if_query_params}

        urls_download_params = map(lambda dict: {**params, **dict}, urls) 
        urls_download_params = list(urls_download_params)

        if fast_download and len(urls) <= 200:
            self.logger.log_info("FAST DOWNLOAD STARTED...\n")
            with ThreadPoolExecutor() as executor:
                values = executor.map(lambda kwargs: self.download_url(**kwargs), urls_download_params)
            results.extend(values)
            return results

        elif fast_download and len(urls) > 200:
            self.logger.log_warning("CANNOT USE FAST DOWNLOAD! TOO MANY URLS. FALLING BACK TO NORMAL DOWNLOAD.\n")

        self.logger.log_info("DOWNLOADS STARTED...")
        values = map(lambda kwargs: self.download_url(**kwargs), urls_download_params)
        results.extend(values)

        if results:
            self.logger.log_info("DOWNLOADS FINISHED!\n")
        else:
            self.logger.log_info("NOTHING DOWNLOADED!\n")
        return results


    def get_links(self, url: str, save_to_file: bool = False, file_path: str = "./links.txt") -> List[str]:
        """
        Gets all the links from the given url.

        Returns a list of links and saves the links to a file if `save_to_file` is set to True.

        Args:
            - url (str): Url to get the links from.
            - save_to_file (bool, optional): Whether to save the links to a file. Defaults to False.
            - file_path (str, optional): File to save the links to. Defaults to "./links.txt".
            Available file formats are: csv, txt, doc, docx, pdf...
        """
        if not isinstance(save_to_file, bool):
            raise TypeError("Invalid type for `save_as_file`")
        if not isinstance(file_path, str):
            raise TypeError("Invalid type for `save_as`")
        result = []
        self.set_base_url(url)
        response = self._make_request(url)
        if response:
            soup = BeautifulSoup(response.content, self.parser)
            links = soup.find_all('a')
            links = list(filter(lambda link: link.get('href') and parse_url(link.get('href')).netloc, links))
            with ThreadPoolExecutor() as executor:
                values = executor.map(lambda arg: self._get_soup_link(*arg), list(map(lambda link: (link, False), links)))
                result.extend(values)

        if save_to_file:
            file_handler = FileHandler(file_path)
            if file_handler.filetype == 'csv':
                url_lists = slice_iterable(result, 1)
                detailed_url_list = [('NO', 'URLS')]
                detailed_url_list.extend([ (c + 1, url_lists[c][0]) for c in range(len(url_lists)) ])
                file_handler.write_to_file(detailed_url_list)
            else:
                for item in result:
                    file_handler.write_to_file(f"{item}\n\n")
        return result


    def get_styles(self, url: str, save_to_file: bool = False, file_path: str = "./styles.txt") -> List[str]:
        """
        Gets all the style links from the given url.

        Returns a list of style links and saves the links to a file if `save_to_file` is set to True.

        Args:
            - url (str): Url to get the styles from.
            - save_to_file (bool, optional): Whether to save the styles to a file. Defaults to False.
            - file_path (str, optional): File to save the links to. Defaults to "./styles.txt".
            Available file formats are: csv, txt, doc, docx, pdf...
        """
        if not isinstance(save_to_file, bool):
            raise TypeError("Invalid type for `save_as_file`")
        if not isinstance(file_path, str):
            raise TypeError("Invalid type for `save_as`")
        result = []
        self.set_base_url(url)
        response = self._make_request(url)
        if response:
            soup = BeautifulSoup(response.content, self.parser)
            styles = soup.find_all('link', {'rel': 'stylesheet'})
            styles += soup.find_all('link', {'type': 'text/css'})
            styles = list(filter(lambda style: style.get('href'), styles))
            with ThreadPoolExecutor() as executor:
                values = executor.map(lambda arg: self._get_soup_element(*arg), list(map(lambda style: (style, 'href', False), styles)))
                result.extend(values)

        if save_to_file:
            file_handler = FileHandler(file_path)
            if file_handler.filetype == 'csv':
                url_lists = slice_iterable(result, 1)
                detailed_url_list = [('NO', 'URLS')]
                detailed_url_list.extend([ (c + 1, url_lists[c][0]) for c in range(len(url_lists)) ])
                file_handler.write_to_file(detailed_url_list)
            else:
                for item in result:
                    file_handler.write_to_file(f"{item}\n\n")
        return result


    def get_scripts(self, url: str, save_to_file: bool = False, file_path: str = "./scripts.txt") -> List[str]:
        """
        Gets all the script links from the given url.

        Returns a list of script links and saves the links to a file if `save_to_file` is set to True.

        Args:
            - url (str): Url to get the scripts from.
            - save_to_file (bool, optional): Whether to save the scripts to a file. Defaults to False.
            - file_path (str, optional): File to save the links to. Defaults to "./scripts.txt".
            Available file formats are: csv, txt, doc, docx, pdf...
        """
        if not isinstance(save_to_file, bool):
            raise TypeError("Invalid type for `save_as_file`")
        if not isinstance(file_path, str):
            raise TypeError("Invalid type for `save_as`")
        result = []
        self.set_base_url(url)
        response = self._make_request(url)
        if response:
            soup = BeautifulSoup(response.content, self.parser)
            scripts = soup.find_all('script')
            scripts = list(filter(lambda script: script.get('src'), scripts))
            with ThreadPoolExecutor() as executor:
                values = executor.map(lambda arg: self._get_soup_element(*arg), list(map(lambda script: (script, 'src', False), scripts)))
                result.extend(values)
        
        if save_to_file:
            file_handler = FileHandler(file_path)
            if file_handler.filetype == 'csv':
                url_lists = slice_iterable(result, 1)
                detailed_url_list = [('NO', 'URLS')]
                detailed_url_list.extend([ (c + 1, url_lists[c][0]) for c in range(len(url_lists)) ])
                file_handler.write_to_file(detailed_url_list)
            else:
                for item in result:
                    file_handler.write_to_file(f"{item}\n\n")
        return result

    
    def get_fonts(self, url: str, save_to_file: bool = False, file_path: str = "./fonts.txt") -> List[str]:
        """
        Gets all the font links from the given url.

        Returns a list of font link and saves the links to a file if `save_to_file` is set to True.

        Args:
            - url (str): Url to get the fonts from.
            - save_to_file (bool, optional): Whether to save the fonts to a file. Defaults to False.
            - file_path (str, optional): File to save the links to. Defaults to "./fonts.txt".
            Available file formats are: csv, txt, doc, docx, pdf...
        """
        if not isinstance(save_to_file, bool):
            raise TypeError("Invalid type for `save_as_file`")
        if not isinstance(file_path, str):
            raise TypeError("Invalid type for `save_as`")
        result = []
        self.set_base_url(url)
        response = self._make_request(url)
        if response:
            soup = BeautifulSoup(response.content, self.parser)
            fonts = soup.find_all('link', {'rel': 'preload'})
            fonts += soup.find_all('link', {'as': 'font'})
            # filter out by font file extensions and href
            font_ext = ['woff', 'woff2', 'ttf', 'otf', 'eot', 'svg']
            fonts = list(filter(lambda font: font.get('href') and parse_url(font.get('href')).path.split('.')[-1] in font_ext, fonts))
            with ThreadPoolExecutor() as executor:
                values = executor.map(lambda arg: self._get_soup_element(*arg), list(map(lambda font: (font, 'href', False), fonts)))
                result.extend(values)

        if save_to_file:
            file_handler = FileHandler(file_path)
            if file_handler.filetype == 'csv':
                url_lists = slice_iterable(result, 1)
                detailed_url_list = [('NO', 'URLS')]
                detailed_url_list.extend([ (c + 1, url_lists[c][0]) for c in range(len(url_lists)) ])
                file_handler.write_to_file(detailed_url_list)
            else:
                for item in result:
                    file_handler.write_to_file(f"{item}\n\n")
        return result

    
    def get_images(self, url: str, save_to_file: bool = False, file_path: str = "./images.txt") -> List[str]:
        """
        Gets all the image links from the given url.

        Returns a list of image links and saves the links to a file if `save_to_file` is set to True.

        Args:
            - url (str): Url to get the images from.
            - save_to_file (bool, optional): Whether to save the images to a file. Defaults to False.
            - file_path (str, optional): File to save the links to. Defaults to "./images.txt".
            Available file formats are: csv, txt, doc, docx, pdf...
        """
        if not isinstance(save_to_file, bool):
            raise TypeError("Invalid type for `save_as_file`")
        if not isinstance(file_path, str):
            raise TypeError("Invalid type for `save_as`")
        result = []
        self.set_base_url(url)
        response = self._make_request(url)
        if response:
            soup = BeautifulSoup(response.content, self.parser)
            images = soup.find_all('img')
            images = list(filter(lambda image: image.get('src'), images))
            with ThreadPoolExecutor() as executor:
                values = executor.map(lambda arg: self._get_soup_element(*arg), list(map(lambda image: (image, 'src', False), images)))
                result.extend(values)

        if save_to_file:
            file_handler = FileHandler(file_path)
            if file_handler.filetype == 'csv':
                url_lists = slice_iterable(result, 1)
                detailed_url_list = [('NO', 'URLS')]
                detailed_url_list.extend([ (c + 1, url_lists[c][0]) for c in range(len(url_lists)) ])
                file_handler.write_to_file(detailed_url_list)
            else:
                for item in result:
                    file_handler.write_to_file(f"{item}\n\n")
        return result


    def get_videos(self, url: str, save_to_file: bool = False, file_path: str = "./videos.txt") -> List[str]:
        """
        Gets all the video links from the given url.

        Returns a list of video links and saves the links to a file if `save_to_file` is set to True.

        Args:
            - url (str): Url to get the videos from.
            - save_to_file (bool, optional): Whether to save the videos to a file. Defaults to False.
            - file_path (str, optional): File to save the links to. Defaults to "./videos.txt".
            Available file formats are: csv, txt, doc, docx, pdf...
        """
        if not isinstance(save_to_file, bool):
            raise TypeError("Invalid type for `save_as_file`")
        if not isinstance(file_path, str):
            raise TypeError("Invalid type for `save_as`")
        result = []
        self.set_base_url(url)
        response = self._make_request(url)
        if response:
            soup = BeautifulSoup(response.content, self.parser)
            videos = soup.find_all('video')
            videos = list(filter(lambda video: video.get('src'), videos))
            with ThreadPoolExecutor() as executor:
                values = executor.map(lambda arg: self._get_soup_element(*arg), list(map(lambda video: (video, 'src', False), videos)))
                result.extend(values)

        if save_to_file:
            file_handler = FileHandler(file_path)
            if file_handler.filetype == 'csv':
                url_lists = slice_iterable(result, 1)
                detailed_url_list = [('NO', 'URLS')]
                detailed_url_list.extend([ (c + 1, url_lists[c][0]) for c in range(len(url_lists)) ])
                file_handler.write_to_file(detailed_url_list)
            else:
                for item in result:
                    file_handler.write_to_file(f"{item}\n\n")
        return result


    def get_audios(self, url: str, save_to_file: bool = False, file_path: str = "./audios.txt") -> List[str]:
        '''
        Gets all the audio links from the given url.

        Returns a list of audio links and saves the links to a file if `save_to_file` is set to True.

        Args:
            - url (str): Url to get the audios from.
            - save_to_file (bool, optional): Whether to save the audios to a file. Defaults to False.
            - file_path (str, optional): File to save the links to. Defaults to "./audios.txt".
            Available file formats are: csv, txt, doc, docx, pdf...
        '''

        if not isinstance(save_to_file, bool):
            raise TypeError("Invalid type for `save_as_file`")
        if not isinstance(file_path, str):
            raise TypeError("Invalid type for `save_as`")
        result = []
        self.set_base_url(url)
        response = self._make_request(url)
        if response:
            soup = BeautifulSoup(response.content, self.parser)
            audios = soup.find_all('audio')
            audios = list(filter(lambda audio: audio.get('src'), audios))
            with ThreadPoolExecutor() as executor:
                values = executor.map(lambda arg: self._get_soup_element(*arg), list(map(lambda audio: (audio, 'src', False), audios)))
                result.extend(values)

        if save_to_file:
            file_handler = FileHandler(file_path)
            if file_handler.filetype == 'csv':
                url_lists = slice_iterable(result, 1)
                detailed_url_list = [('NO', 'URLS')]
                detailed_url_list.extend([ (c + 1, url_lists[c][0]) for c in range(len(url_lists)) ])
                file_handler.write_to_file(detailed_url_list)
            else:
                for item in result:
                    file_handler.write_to_file(f"{item}\n\n")
        return result
        

    def _get_soup_element(self, element: Tag, src: str, download: bool = True):
        '''
        Get the element src and download the file If `download` is set to True.

        Args:
            element (Tag): Element to be checked.
            src (str): Element src attribute.
            download (bool, optional): Whether to download the file. Defaults to True.
        
        '''
        if not isinstance(element, Tag):
            raise TypeError('`element` should be of type Tag')

        element_src: str = element.attrs.get(src)
        if element.name.lower() == 'use':
            element_src = element_src.split('#')[0]

        _base_url = self._base_url

        if element_src:
            element_src = element_src.replace('..', '').replace('./', '/')
            if element_src.startswith('//'):
                element_src = element_src.replace('//', '/')
            
            url_obj = parse_url(element_src)
            # Get the actual url
            if (url_obj.scheme and url_obj.netloc):
                actual_url = url_obj.url
            elif url_obj.netloc and not url_obj.scheme:
                actual_url = f"http://{url_obj.url}"
            else:
                actual_url = urljoin(_base_url, url_obj.url)
            
            actual_url_obj = parse_url(actual_url)
            _base_url_obj = parse_url(_base_url)

            # Only scrape internal links, that is, links associated with the website being scraped only.
            if download and (_base_url_obj.netloc and actual_url_obj.netloc) and _base_url_obj.netloc in actual_url_obj.netloc:
                storage_path, _ , _= self.download_url(url=actual_url, check_ext=False, unique_if_query_params=True)

                # change the element's src to be compatible with the scraped website
                if storage_path:
                    element[src] = storage_path.replace('\\', '/')
            elif not download:
                return actual_url_obj.url
        

    def _get_associated_files(self, soup: BeautifulSoup):
        '''
        Scrapes all the soup tags present in `self.scrapable_tags`
        
        Args:
            soup (BeautifulSoup): BeautifulSoup object to be scraped.
        '''
        if not isinstance(soup, BeautifulSoup):
            raise TypeError("`soup` should be of type BeautifulSoup")
        
        scrapable_tags = self.scrapable_tags
        elements: ResultSet = None
        
        for scrapable_tag in scrapable_tags:
            if len(scrapable_tag.split('|')) == 1:
                tag_name = scrapable_tag
                elements = soup.find_all(tag_name)

            elif len(scrapable_tag.split('|')) == 2:
                tag_name = scrapable_tag.split('|')[0]
                attrs = json.loads(scrapable_tag.split('|')[1])
                elements = soup.find_all(tag_name, attrs)

            if elements:
                self.logger.log_info(f'GETTING "{scrapable_tag}" ELEMENTS... \n' )
                for element in elements:
                    src = self._get_element_src_by_tag_name(tag_name)
                    if element.attrs.get(src):
                        self._get_soup_element(element, src)


    def _get_soup_link(self, link: Tag, download: bool = True):
        '''
        Get the link href and download the file
        
        Args:
            link (Tag): Link to be scraped.
            download (bool, optional): Whether to download the file. Defaults to True.
        '''
        if not isinstance(link, Tag):
            raise TypeError('`link` should be of type Tag')
        if not link.name == 'a':
            raise ValueError('`link` should be an HTML "a" tag')

        link_href = link.get('href', None)
        actual_url = None
        storage_path = None
        html_filename = self.html_filename
        _base_url = self._base_url
        
        if link_href:
            url_obj = parse_url(link_href)
            # Get actual url
            if (url_obj.scheme and url_obj.netloc):
                actual_url = url_obj.url
            elif url_obj.netloc and not url_obj.scheme:
                actual_url = f"http://{url_obj.url}"
            else:
                actual_url = urljoin(_base_url, url_obj.url)

            actual_url_obj = parse_url(actual_url)
            _base_url_obj = parse_url(_base_url)

            # Only scrape internal links, that is, links associated with the website being scraped only.
            if download and (_base_url_obj.netloc and actual_url_obj.netloc) and _base_url_obj.netloc in actual_url_obj.netloc:
                storage_path, new_file, html_filename = self.download_url(url=actual_url, save_as=html_filename, check_ext=False, unique_if_query_params=True)
                if new_file:
                    new_soup = BeautifulSoup(new_file.read(), self.parser)
                    self._get_associated_files(new_soup)

                # change the link's href to be compatible with the scraped website
                if storage_path:
                    link['href'] = storage_path.replace('\\', '/')
            elif not download:
                return actual_url_obj.url

        return (actual_url, storage_path, html_filename)


