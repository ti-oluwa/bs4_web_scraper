from typing import Any, Dict, List
import requests
import os
import io
import random
import time
import json
import string
import math
import copy
from bs4 import BeautifulSoup
from bs4.element import Tag, ResultSet
from urllib3.util.url import parse_url, Url
from urllib.parse import urljoin
import translators as ts
from translators.server import tss
from concurrent.futures import ThreadPoolExecutor

from .utils import Logger, RequestLimitSetting, slice_list, get_current_time

# DEFAULT USER-AGENTS THAT CAN BE USED IN PLACE OF THE RANDOM USER-AGENTS
# USER_AGENTS = [
#    "Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
#    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36 Edg/109.0.1518.78",
# ]


# SCRAPE SITES WITH PAGINATION

class BS4WebScraper:
    """
    ### BeautifulSoup4 web scraper class with support for authentication and translation.

    #### Example:
    To create an instance, do:
        >>> bs4_scraper = BS4WebScraper(parser='lxml', html_filename='google.html',
                            no_of_requests_before_pause=50, scrape_session_pause_duration='auto',
                            base_storage_dir='./google', storage_path='/', 
                            log_filename='google.log', ...)
    #              
        >>> bs4_scraper.scrape(url='https://www.google.com', scrape_depth=0)
            'google.html' saves to './google/google.html'

    #

    #### NOTE: On instantiation of the class, a new request session is created. This session is used to make all related requests.

    @param str `parser`: HTML or HTML/XML parser for BeautifulSoup. Default is "lxml", "html.parser" is another suitable parser.

    @param str `html_filename`: Default name used to save '*.html' files.

    @param int `no_of_requests_before_pause`: Defines the number of requests that can be made before a pause is taken.
    This is implemented to regulate the request rate to websites in order to avoid hitting the website's server at very high rates
    which can either to lead to a 429 response code, Permission denied error or complete access block. Default is 20.

    @param int `scrape_session_pause_duration`: Number of second for which a pause is observed after the max request 
    count has been reached before a reset. Defaults to "auto" but the minimum pause duration allowed is 3 seconds. When set to "auto", 
    the scraper decides the suitable pause duration based on `no_of_requests_before_pause`.

    @param int `max_no_of_retries`: Maximum number of times a failed request will be retried before moving on.

    #### `no_of_requests_before_pause`, `scrape_session_pause_duration` and `max_no_of_retries` are used to instantiate a `RequestLimitSetting` for the class instance.

    @param str `base_storage_dir`: The directory where the folder containing scraped website will be stored. Defaults to 
    the current directory.

    @param str `storage_path`: Path where the base(index) HTML file will be saved with respect to the `base_storage_dir`.
    Defaults to directly inside the `base_storage_dir`.

    @param str | path `log_filename`: Name of the file logs will be written into. Defaults to 'bs4_scraper.log'.
    This can also be a path to a directory in which the log file should be saved or the path to an already existing log file.
    #### For instance:
    >>> bs4_scraper = BS4WebScraper(..., log_filename="/<directory_path>/<filename>/")

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

    @attr str `translator_target_language`: The language the scraped pages will be translated to as provided in the scrape function.

    @attr str `translator_source_language`: The origin language of the the scraped pages.

    @attr list `_translatable_elements`: A list of HTML elements that might contain translatable text.

    @attr dict `translator_supported_languages`: A dictionary of all languages supported by the chosen translation engine.

    @attr str `_base_url`: The base URL of the website being scraped.

    @attr int `_level_reached`: The depth or number of levels successfully scraped.

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
    _request_session: requests.Session = requests.Session()
    _request_user_agent: str = None
    logger: Logger = Logger('bs4_scraper.log')
    translation_engine: str = 'google'
    translator_target_language: str = None
    translator_source_language: str = None
    _translatable_elements: List[str] = [
                                'h1', 'u', 's', 'abbr', 'del', 'pre', 'h5', 'sub', 'kbd', 'li', 
                                'dd', 'textarea', 'dt', 'input', 'em', 'sup', 'label', 'button', 'h6', 
                                'title', 'dfn', 'th', 'acronym', 'cite', 'samp', 'td', 'p', 'ins', 'big', 
                                'caption', 'bdo', 'var', 'h3', 'tt', 'address', 'h4', 'legend', 'i', 
                                'small', 'b', 'q', 'option', 'code', 'h2', 'a', 'strong', 'span',
                            ]
    scrapable_tags = [
                    'script', 'link|{"rel": "stylesheet"}', 'img', 'use', 
                    'video', 'link|{"as": "font"}',
                    'link|{"rel": "shortcut"}', 'link|{"rel": "icon"}',
                    'link|{"rel": "shortcut icon"}', 'link|{"rel": "apple-touch-icon"}',
                    'link|{"type": "image/x-icon"}', 'link|{"type": "image/png"}',
                    'link|{"type": "image/jpg"}', 'link|{"type": "image/jpeg"}',
                    'link|{"type": "image/svg"}', 'link|{"type": "image/webp"}',
                ]

    _trans_cache: Dict[str, str] = dict()

    def __init__(self, parser: str = 'lxml', html_filename: str = "index.html", 
                no_of_requests_before_pause: int = 20, scrape_session_pause_duration: int | float | Any = "auto",
                max_no_of_retries: int = 2, base_storage_dir: str = '.', storage_path: str = '', 
                log_filename: str | None = None, translation_engine: str | None = 'google') -> None:

        if not isinstance(parser, str):
            raise ValueError('`parser` should be of type str')
        if not isinstance(html_filename, str) or not html_filename.endswith('.html'):
            raise ValueError('`html_filename` should be of type str and should take the format `<filename>.html`.')
        if not isinstance(storage_path, str):
            raise ValueError('`storage_path` should be of type str')
        if not isinstance(base_storage_dir, str):
            raise ValueError('`base_storage_dir` should be of type str')
        if not isinstance(no_of_requests_before_pause, int):
            raise ValueError('`no_of_requests_before_pause` should be of type int')
        if not isinstance(scrape_session_pause_duration, (int, float, str)):
            raise ValueError('`scrape_session_pause_duration` should be of type int or float')
        if isinstance(scrape_session_pause_duration, str) and scrape_session_pause_duration != 'auto':
            raise ValueError('The only accepted string value for `scrape_session_pause_duration` is `auto`.')
        if scrape_session_pause_duration == 'auto':
            scrape_session_pause_duration = math.ceil((3 / 20) * no_of_requests_before_pause)
        if scrape_session_pause_duration < 3:
            raise Exception("`scrape_session_pause_duration` cannot be less than 3 seconds")
        if log_filename and not isinstance(log_filename, str):
            raise ValueError('`log_filename` should be of type str')

        if translation_engine and not isinstance(translation_engine, str):
            raise ValueError('`translation_engine` should be of type str')
        if translation_engine and translation_engine not in ts.translators_pool:
            raise Exception("Unsupported translation translation_engine")

        if log_filename:
            log_filename.replace('/', '\\')
            if '\\' in log_filename:
                os.makedirs(os.path.dirname(log_filename), exist_ok=True)
            self.logger = Logger(log_filename)

        self.translation_engine = translation_engine
        self.parser = parser
        self.html_filename = html_filename
        self._base_html_filename = html_filename
        self.no_of_requests_before_pause = no_of_requests_before_pause
        self.scrape_session_pause_duration = scrape_session_pause_duration
        self.max_no_of_retries = max_no_of_retries
        base_storage_dir = base_storage_dir.replace('/', '\\')
        self.base_storage_dir = base_storage_dir
        self.storage_path = storage_path
        self.url_query_params = []
        self.request_limit_setting = RequestLimitSetting(self.no_of_requests_before_pause, self.scrape_session_pause_duration, self.max_no_of_retries, self.logger)

    @property
    def translator_supported_languages(self) -> dict:
        if self.translation_engine:
            args = ('yes','en', 'zh')
            func = lambda f: getattr(tss, f"{self.translation_engine}")(*f)
            func(args)
            return getattr(tss, f"_{self.translation_engine}").language_map
        return dict()


    def _get_base_url(self, url: str) -> str:
        '''
        Returns a base url containing only the host, scheme and port

        Args:
            url (str): The url to be parsed. The url should be of the format `http://www.example.com:80/path/to/resource?query=string`,
            The base url will be `http://www.example.com:80`.
        '''
        if not isinstance(url, str):
            raise ValueError('`url` should be of type str')
        url_obj = parse_url(url)
        if not (url_obj.host and url_obj.scheme):
            raise ValueError('Invalid url!')

        new_url_obj = Url(scheme=url_obj.scheme, host=url_obj.host)
        return new_url_obj.url

    
    def _validate_auth_credentials(self, credentials: Dict[str, str]) -> None:
        '''
        Validates the authentication credentials.

        Returns the authentication URL.

        Args:
            credentials (dict): A dictionary containing the authentication credentials.
        '''
        if not isinstance(credentials, dict):
            raise ValueError('Invalid type for `credentials`')

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
                raise ValueError(f'Invalid type for `{key}`. `{key}` should be of type str')

        auth_url_obj = parse_url(credentials.get("auth_url"))
        if not (auth_url_obj.host and auth_url_obj.scheme):
            raise Exception("`auth_url` is not a valid URL")
     
        if parse_url(self._base_url).host not in auth_url_obj.host:
            raise Exception("`auth_url` might be invalid as it is not related to `self._base_url`. Please re-check credentials.")

        return auth_url_obj.url


    def _set_auth_credentials(self, credentials: Dict[str, str]) -> None:
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
            raise ValueError('Invalid type for `credentials`')

        self._auth_url = self._validate_auth_credentials(credentials)
        _credentials = {}
        _credentials[credentials['auth_username_field']] = credentials['auth_username']
        _credentials[credentials['auth_password_field']] = credentials['auth_password']
        self._auth_credentials = _credentials


    def _translate_text(self, text: str, src_lang: str="auto", target_lang: str="en") -> str:
        '''
        Translate text from `src_lang` to `target_lang` using `self.translator`.

        Returns translated text.

        Args:
            text (str): Text to be translated
            src_lang (str, optional): Source language. Defaults to "auto".
            target_lang (str, optional): Target language. Defaults to "en".

        '''
        if not isinstance(text, str):
            raise ValueError("Invalid type for `text`")
        if not isinstance(src_lang, str):
            raise ValueError("Invalid type for `src_lang`")
        if not isinstance(target_lang, str):
            raise ValueError("Invalid type for `target_lang`")

        translated_text = ts.translate_text(query_text=text, to_language=target_lang, 
                                            from_language=src_lang, translator=self.translation_engine)
        return translated_text

    # NOT FUNCTIONAL FOR NOW
    # def _translate_html(self, html: str | bytes, src_lang: str="auto", target_lang: str="en"):
    #     '''
    #     Translates the html content from `src_lang` to `target_lang` using `self.translator`.

    #     Returns translated html.
    #     Args:
    #         html (str | bytes): HTML content to be translated
    #         src_lang (str, optional): Source language. Defaults to "auto".
    #         target_lang (str, optional): Target language. Defaults to "en".
    #     '''
    #     if not isinstance(html, (str, bytes)):
    #         raise ValueError("Invalid type for `html`")
    #     if not isinstance(src_lang, str):
    #         raise ValueError("Invalid type for `src_lang`")
    #     if not isinstance(target_lang, str):
    #         raise ValueError("Invalid type for `target_lang`")

    #     html = html.decode('utf-8') if isinstance(html, bytes) else html
    #     translated_html = ts.translate_html(html_text=html, to_language=target_lang, from_language=src_lang, translator=self.translation_engine)
    #     print("TRANSLATION: ", translated_html)
    #     return translated_html


    def _translate_soup_element(self, element: Tag, _ct: int = 0) -> None:
        '''
        Translates the text of a BeautifulSoup element.

        Args:
            element (bs4.element.Tag): The element whose text is to be translated.
            _ct (int, optional): The number of times the function has been called recursively. Defaults to 0.
            Do not pass this argument manually.
        
        '''
        if not isinstance(element, Tag):
            raise ValueError("Invalid type for `element`")
        if not isinstance(_ct, int):
            raise ValueError("Invalid type for `_ct`")

        if element.string.strip():
            initial_string = copy.copy(element.string)
            cached_translation = self._trans_cache.get(element.string, None)
            if cached_translation:
                element.string.replace_with(cached_translation)
            else:
                try:
                    translation = self._translate_text(text=element.string, target_lang=self.translator_target_language)
                    element.string.replace_with(translation)
                except Exception as e:
                    self.logger.log_error(f'{e}\n')
                    _ct += 1
                    time.sleep(4 * _ct)
                    if _ct <= 3:
                        return self._translate_soup_element(element, _ct)
                else:
                    self._trans_cache[initial_string] = translation


    def _lang_is_supported(self, lang_code: str) -> bool:
        '''
        Check if the specified language code is supported by `self.translator`
        
        Returns True if supported, else False.

        Args:
            lang_code (str): The language code to check.
        
        '''
        if not isinstance(lang_code, str):
            raise ValueError("Invalid type for `lang_code`")
        lang_code = lang_code.strip().lower()
        if not lang_code:
            raise ValueError("`lang_code` cannot be empty")
        return bool(self.translator_supported_languages.get(lang_code, None)) if self.translator_supported_languages else False


    def _set_translator_target(self, target_lang: str) -> None:
        '''
        Sets the instance's target language for translation.

        Args:
            target_lang (str): The target language for translation.
        
        '''
        if target_lang and not isinstance(target_lang, str):
            raise ValueError('`target_lang` should be of type str')
        if target_lang and not self._lang_is_supported(target_lang):
            raise Exception("Unsupported target language for translation")

        self.translator_target_language = target_lang.strip().lower()


    def _set_translator_source(self, src_lang: str) -> None:
        '''
        Sets the instance's source language for translation.

        Args:
            src_lang (str): The source language for translation.
        
        '''
        if src_lang and not isinstance(src_lang, str):
            raise ValueError('`src_lang` should be of type str')
        if src_lang and not self._lang_is_supported(src_lang):
            raise Exception("Unsupported source language for translation")

        self.translator_source_language = src_lang.strip().lower()
        

    def _scrape(self, url: str, scrape_depth: int = 1, credentials: Dict[str, str] | None = None, translate_to: str = None) -> None:
        '''
        Main scraping method.
        
        NOTE: This method is not meant to be called directly. It is called by the `scrape` method.
        Use the `scrape` method instead.
        '''
        if not isinstance(url, str):
            raise ValueError('`url` should be of type str')

        _url_obj = parse_url(url)
        if not (_url_obj.host and _url_obj.scheme):
            raise ValueError('Invalid url! url should start with "http://" or "https://"')
        if not isinstance(scrape_depth, int):
            raise ValueError('`scrape_depth` should be of type int')

        # use proper url format
        url = _url_obj.url

        # set translator target lang
        if translate_to:
            self._set_translator_target(translate_to)

        # set the base url of the website
        if self._level_reached == 0:
            self._base_url = self._get_base_url(url)
        if credentials:
            self._set_auth_credentials(credentials)
            
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
        index_file.close()

        # create soup
        soup = BeautifulSoup(file_content, self.parser)

        # get all associated files ('*js', '*.css', font files, ...)
        self._get_associated_files(soup)

        if scrape_depth > 0:
            links = soup.find_all('a')

        # get links
        if links:
            self.logger.log_info(f'~~~SCRAPING AT LEVEL {self._level_reached + 1}~~~\n')
            for link in links:
                page_link_detail = self._get_soup_link(link)
                page_links_details.append(page_link_detail)

            if self._level_reached == 0:
                self._level_reached += 1  

        # Create new base file with updated link_href, script_src, image_src, href's etc.
        self.logger.log_info("REWRITING BASE HTML FILE WITH UPDATED ELEMENT ATTRIBUTES\n")
        self._create_file(filename=self._base_html_filename, storage_path=self.storage_path, 
                            content=soup.prettify(formatter='html'), create_mode='w', 
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
        Only scrapes includes internal links, images, scripts, use, videos and font files.
        
        @param str `url`: The url of the website or webpage to be scraped.

        @param int `scrape_depth`: The number of levels deep to scrape. Defaults to 1.

        @param dict `credentials`: Authentication or login details for website.

        @param str `translate_to`: Language code for the language scraped content will be translated to. The source language
        is automatically detected by `self.translator`.

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
        >>> print(bs4_scraper.translator_supported_languages)
        >>> # {'af': 'afrikaans', 'sq': 'albanian', 'am': 'amharic', ...}

        Make sure to set the `translation_engine` argument to the engine you want to use for translation.

        For instance to translate to 'amharic', do:
        >>> bs4_scraper.scrape(..., translate_to="am")

        #### NOTE: The `translate_to` argument is case insensitive.

        #
        """

        self.logger.log_info("STARTING SCRAPING ACTIVITY...\n")
        self.logger.log_info(f"SCRAPING DEPTH: {scrape_depth if scrape_depth > 0 else 'BASE LEVEL'}\n")
        if translate_to:
            self.logger.log_info(f"TRANSLATION ENGINE: {self.translation_engine.upper()}\n")
            self.logger.log_info(f"TRANSLATING TO: {translate_to.upper()}\n")

        print(f"[{get_current_time()}] - STARTING SCRAPING ACTIVITY...\n")
        print(f"[{get_current_time()}] - SCRAPING DEPTH: {scrape_depth if scrape_depth > 0 else 'BASE LEVEL'}\n")
        if translate_to:
            print(f"[{get_current_time()}] - TRANSLATION ENGINE: {self.translation_engine.upper()}\n")
            print(f"[{get_current_time()}] - TRANSLATING TO: {translate_to.upper()}\n")

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
            print(f"[{get_current_time()}] - SCRAPING COMPLETED IN {(time_taken / 60):.2f} MINUTES\n")
            self.logger.log_info(f"SCRAPING COMPLETED IN {(time_taken/ 60):.2f} SECONDS\n")
        else:
            print(f"[{get_current_time()}] - SCRAPING COMPLETED IN {time_taken:.2f} SECONDS\n")
            self.logger.log_info(f"SCRAPING COMPLETED IN {time_taken:.2f} SECONDS\n")


    def generate_random_user_agents(self) -> list:
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


    def get_request_headers(self) -> dict:
        '''Returns a suitable request header'''
        if not isinstance(self.generate_random_user_agents(), list):
            raise Exception("Invalid return type for `self.generate_random_user_agents`")

        if self._auth_credentials:
            if not self._request_user_agent:
                user_agents = self.generate_random_user_agents()
                random.shuffle(user_agents)
                self._request_user_agent = random.choice(user_agents)
        else:
            user_agents = self.generate_random_user_agents()
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


    def _make_request(self, url: str) -> requests.Response:  
        '''
        Makes a GET request to url given, authenticates requests and limits request rate based on limit setting if provided. 
        
        Returns response if OK.
        Args:
            url (str): url to make request to
        '''  
        if not isinstance(url, str):
            raise ValueError('url is not a string')

        request_limit_setting = self.request_limit_setting
        headers = self.get_request_headers()
        if not isinstance(headers, dict):
            raise Exception("Invalid return type for `self.get_request_headers`")

        self._request_session.headers.update(headers)        

        # authenticate if credentials are provided
        if not self._is_authenticated and self._auth_credentials:
            self.logger.log_info(f'AUTHENTICATING AT... --> {self._auth_url}\n')
            resp = self._request_session.get(url=self._auth_url) 
            auth_details = self._auth_credentials
            auth_details['csrfmiddlewaretoken'] = resp.cookies.get('csrftoken')
            resp = self._request_session.post(url=self._auth_url, data=auth_details)
            self._is_authenticated = resp.ok

            if self._is_authenticated:
                self.logger.log_info('AUTHENTICATED!!!\n')
            else:
                self.logger.log_error('AUTHENTICATION FAILED!!!\n')

        if request_limit_setting is None:
            self.logger.log_info('GETTING --> %s \n' % url)
            response = self._request_session.get(url, headers=headers)
            if response.status_code != 200:
                self.logger.log_warning(f"REQUEST GOT RESPONSE CODE -> {response.status_code} \n")
                return self._make_request(url)
            return response

        else:
            if request_limit_setting.can_make_requests == True:
                self.logger.log_info("NUMBER OF AVAILABLE REQUEST: %s\n" % str(request_limit_setting.no_of_available_request))
                self.logger.log_info('GETTING --> %s \n' % url)
                response = self._request_session.get(url)

                if response.status_code == 200:
                    self.logger.log_info('SUCCESS: REQUEST OK \n')
                    request_limit_setting.request_made()
                    return response
                else:
                    self.logger.log_warning(f"REQUEST GOT RESPONSE CODE -> {response.status_code} \n")
                    request_limit_setting.request_made()
                    if request_limit_setting.can_retry and response.status_code not in [403, 404]:
                        request_limit_setting.got_response_error()
                        self.logger.log_info('RETRYING... \n')
                        time.sleep(request_limit_setting.pause_duration * 5)
                        return self._make_request(url, request_limit_setting)

                    elif not request_limit_setting.can_retry:
                        self.logger.log_warning("MAXIMUM NUMBER OF RETRIES REACHED! MOVING ON >>> \n")
                        request_limit_setting.reset_max_retry()
                    return None

            else:
                self.logger.log_info('RETRYING... \n')
                time.sleep(request_limit_setting.pause_duration)
                return self._make_request(url, request_limit_setting)
    

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
            raise ValueError("Invalid argument type for `filename`")

        if not isinstance(storage_path, str):
            raise ValueError("Invalid argument type for `storage_path`")

        if not isinstance(create_mode, str):
            raise ValueError("Invalid argument type for `create_mode`")

        if not isinstance(content, (bytes, str)):
            raise ValueError('Argument `content` can only be bytes or str.')

        if not isinstance(encoding, str) and encoding is not None:
            raise ValueError('Argument `encoding` can only be NoneType or str.')

        if create_mode not in ['x', 'xb', 'w', 'wb']:
            raise ValueError("`%s` is not an allowed mode. Allowed modes: 'x', 'xb', 'w', 'wb'." % create_mode)

        if create_mode in ["x", "w"] and encoding is None:
            raise ValueError("Encoding cannot be NoneType when `create_mode` is 'x'.")

        # Translate
        if translate and (self.translator_target_language and filename.endswith('.html')):
            self.logger.log_info('TRANSLATING CONTENT...\n')
            soup = BeautifulSoup(content, self.parser)
            with ThreadPoolExecutor() as executor:
                for list_item in slice_list(soup.findAll(self._translatable_elements), 50):
                    executor.map(self._translate_soup_element, list_item)
                    time.sleep(2)
            
            content = soup.prettify()
            # NOT FUNCTIONAL FOR NOW
            # content = self._translate_html(content, target_lang=self.translator_target_language)
            self.logger.log_info("CONTENT TRANSLATED!\n")

            if create_mode in ['xb', 'wb'] and isinstance(content, str):
                self.logger.log_info('RE-ENCODING CONTENT...\n')
                content = content.encode('utf-8')

        base_storage_dir = self.base_storage_dir
        write_mode = "w"
        read_mode = "r"
        if create_mode.endswith('b'):
            write_mode = "wb"
            read_mode = "rb"

        try:
            dir_path = f"{base_storage_dir}\{storage_path}"
            try:
                os.makedirs(dir_path, exist_ok=True)
            except FileExistsError:
                pass

            with open(f"{dir_path}\{filename}", create_mode, encoding=encoding) as f:
                if f.writable():
                    f.write(content)
                    f.close()
                    file = open(f"{dir_path}\{filename}", read_mode, encoding=encoding)
                    return file

                else:
                    raise Exception('File does not support write')
        
        except FileExistsError:
            return self._create_file(filename, storage_path, content, write_mode, encoding)
            

    def _parse_storage_path(self, url_obj: Url) -> str:
        '''
        Returns a suitable storage path from a Url.

        Args:
            url_obj (Url): Url object to be parsed.
        '''
        if not isinstance(url_obj, Url):
            raise ValueError('`url_obj` should be of type Url')

        url_path = url_obj.path or ''
        return url_path.replace('/', '\\')


    def _get_element_src_by_tag_name(self, tag_name: str) -> str:
        '''
        Return the tag attribute that contains the src url/path.

        Args:
            tag_name (str): Tag name to be checked.
        
        '''
        if not isinstance(tag_name, str):
            raise ValueError('`tag_name` should be of type str')
        tag_name = tag_name.lower()

        if tag_name in ['img', 'script', 'video']:
            return 'src'
        if tag_name in ['use', 'link']:
            return 'href'
        

    def _get_soup_element(self, element: Tag, element_tag_name: str, src: str) -> None:
        '''
        Get the element src and download the file.

        Args:
            element (Tag): Element to be checked.
            element_tag_name (str): Element tag name.
            src (str): Element src attribute.
        
        '''
        if not isinstance(element, Tag):
            raise ValueError('`element` should be of type Tag')

        element_src: str = element.attrs.get(src)
        if element_tag_name.lower() == 'use':
            element_src = element_src.split('#')[0]

        response = None
        has_query_params = False
        base_storage_dir = self.base_storage_dir
        _base_url = self._base_url

        if element_src:
            element_src = element_src.replace('..', '').replace('./', '/')
            if element_src.startswith('//'):
                element_src = element_src.replace('//', '/')
            
            url_obj = parse_url(element_src)
            element_name = url_obj.path.split('/')[-1]

            # check if element src has query params
            if url_obj.query:
                has_query_params = True

            if (url_obj.scheme and url_obj.host):
                actual_url = url_obj.url

            elif url_obj.host and not url_obj.scheme:
                actual_url = f"http://{url_obj.url}"

            else:
                actual_url = urljoin(_base_url, url_obj.url)

            actual_url_obj = parse_url(actual_url)
            _base_url_obj = parse_url(_base_url)

            # Only scrape internal links, that is, links associated with the website being scraped only.
            if (_base_url_obj.host and actual_url_obj.host) and _base_url_obj.host in actual_url_obj.host:
                new_storage_path = self._parse_storage_path(actual_url_obj).replace(element_name, '')
                
                if has_query_params:
                    element_name = self._generate_unique_filename(element_name)
                full_path = f"{base_storage_dir}\{new_storage_path}\{element_name}"

                if not has_query_params or (url_obj.query not in self.url_query_params):
                    if os.path.exists(full_path) is False:
                        response = self._make_request(actual_url)
                    else:
                        self.logger.log_info("`%s` ALREADY EXISTS! \n" % full_path)

                if response:
                    _ = self._create_file(filename=element_name, storage_path=new_storage_path, content=response.content)
                    if has_query_params:
                        self.url_query_params.append(url_obj.query) 

                    # change the element's src to be compatible with the scraped website
                    element['href'] = full_path.replace('\\', '/')
        

    def _get_associated_files(self, soup: BeautifulSoup) -> None:
        '''
        Scrapes all the soup tags present in `self.scrapable_tags`
        
        Args:
            soup (BeautifulSoup): BeautifulSoup object to be scraped.
        '''
        if not isinstance(soup, BeautifulSoup):
            raise ValueError("`soup` should be of type BeautifulSoup")
        
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
                        self._get_soup_element(element, tag_name, src)


    def _generate_unique_id(self) -> str:
        '''Returns a random string of random length'''
        sample = list('0123456789' + string.ascii_lowercase)
        id = "".join(random.choices(sample, k=random.randint(4, 6)))
        return id


    def _generate_unique_filename(self, old_filename: str) -> str:
        '''
        Returns the old filename but with a random id to make it unique.

        Args:
            old_filename (str): Old filename to be modified.
        
        '''
        if not isinstance(old_filename, str):
            raise ValueError('`old_filename` should be of type str')

        name, ext = os.path.splitext(old_filename)
        unique_filename = f"{name}{self._generate_unique_id()}{ext}"
        return unique_filename


    def _get_soup_link(self, link: Tag) -> None:
        '''
        Get the link href and download the file
        
        Args:
            link (Tag): Link to be scraped.
        
        '''
        if not isinstance(link, Tag):
            raise ValueError('`link` should be of type Tag')

        link_href = link.get('href', None)
        actual_url = None
        new_storage_path = None
        response = None
        has_query_params = False

        html_filename = self.html_filename
        base_storage_dir = self.base_storage_dir
        _base_url = self._base_url
        
        if link_href:
            url_obj = parse_url(link_href)

            # check if link href has query params
            if url_obj.query:
                has_query_params = True

            if (url_obj.scheme and url_obj.host):
                actual_url = url_obj.url

            elif url_obj.host and not url_obj.scheme:
                actual_url = f"http://{url_obj.url}"

            else:
                actual_url = urljoin(_base_url, url_obj.url)

            actual_url_obj = parse_url(actual_url)
            _base_url_obj = parse_url(_base_url)

            # Only scrape internal links, that is, links associated with the website being scraped only.
            if (_base_url_obj.host and actual_url_obj.host) and _base_url_obj.host in actual_url_obj.host:
                new_storage_path = self._parse_storage_path(actual_url_obj)
            
                if has_query_params:
                    html_filename = self._generate_unique_filename(html_filename)
                    
                full_path = f"{base_storage_dir}\{new_storage_path}\{html_filename}"

                if not has_query_params or (url_obj.query not in self.url_query_params):
                    if os.path.exists(full_path) is False:
                        response = self._make_request(actual_url)
                    else:
                        self.logger.log_info("`%s` ALREADY EXISTS! \n" % full_path)

                if response:
                    filename = html_filename
                    name, ext = os.path.splitext((actual_url_obj.path or '').split('/')[-1])
                    if ext and ext != '.html':
                        filename = f'{name}{ext}'

                    if ext and ext == '.html':
                        new_file = self._create_file(filename=filename, storage_path=new_storage_path, 
                                        content=response.text, create_mode='x', encoding='utf-8')
                    else:
                        new_file = self._create_file(filename=filename, storage_path=new_storage_path, content=response.content)
                
                    if new_file:
                        if has_query_params:
                            self.url_query_params.append(url_obj.query) 

                        new_soup = BeautifulSoup(new_file.read(), self.parser)
                        self._get_associated_files(new_soup)

                    # change the link's href to be compatible with the scraped website
                    link['href'] = full_path.replace('\\', '/')

        return (actual_url, new_storage_path, html_filename)




if "__name__" == "__main__":
    bs4_base_scraper = BS4WebScraper()
