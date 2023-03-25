"""
DESCRIPTION: ::
    This module contains the BS4WebScraper class which is the base class for creating scraper instances 
    used to scrape websites.

    Don't make high frequency requests! Scrape responsibly!
    If you are using this module to scrape websites for commercial purposes, please consider supporting the
    websites you are scraping by making a donation.
"""
import os
from typing import (Dict, List, Iterable, Any, IO)
import time
from concurrent.futures import ThreadPoolExecutor

from . import utils
from .base import BS4BaseScraper
from .file_handler import FileHandler


class BS4WebScraper(BS4BaseScraper):
    """
    #### BeautifulSoup4 web scraper class with support for authentication and translation.

    #### Instantiation and Example Usage: ::
    >>> bs4_scraper = BS4WebScraper(parser='lxml', html_filename='google.html',
                        no_of_requests_before_pause=50, scrape_session_pause_duration='auto',
                        base_storage_dir='./google', storage_path='/', 
                        log_filepath='google.log', ...)
    >>> bs4_scraper.scrape(url='https://www.google.com', scrape_depth=0)
        # 'google.html' saves to './google/google.html'
        # A log file 'google.log' is created in the './google' directory


    NOTE: On instantiation of the class, a new request session is created. This session is used to make all related requests.

    #### Parameters:
    @param str `parser`: HTML or HTML/XML parser for BeautifulSoup. Default is "lxml", "html.parser" is another suitable parser.

    Available parsers: ::
    * "lxml"
    * "lxml-xml"
    * "html.parser"
    * "html5lib"

    or it may be the type of markup to be scraped::
    * "html"
    * "html5"
    * "xml"
    
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

    `no_of_requests_before_pause`, `scrape_session_pause_duration` and `max_no_of_retries` are used to instantiate a `RequestLimitSetting` for the class instance.

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

    
    def scrape(self, url: str, scrape_depth: int = 1, credentials: Dict[str, str] | None=None, translate_to: str = None) -> None:
        """
        #### Wrapper function for the private `_scrape` function of the class.

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
        self.log("STARTING SCRAPING ACTIVITY...\n")
        self.log(f"SCRAPING DEPTH: {scrape_depth if scrape_depth > 0 else 'BASE LEVEL'}\n")
        if translate_to:
            self.log(f"TRANSLATION ENGINE: {self.translator.translation_engine.upper()}\n")
            self.log(f"TRANSLATING TO: {translate_to.upper()}\n")

        start_time = time.perf_counter()
        super()._scrape(url, scrape_depth, credentials, translate_to)
        finish_time = time.perf_counter()
        time_taken = finish_time - start_time

        if self._level_reached > 0:
            self.log(f"SCRAPED {self._level_reached} LEVEL{'S'[:self._level_reached^1]} SUCCESSFULLY! \n")
        else:
            self.log("SCRAPED BASE LEVEL SUCCESSFULLY! \n")

        if time_taken >= 60:
            self.log(f"SCRAPING COMPLETED IN {(time_taken / 60):.2f} MINUTES\n")
        else:
            self.log(f"SCRAPING COMPLETED IN {time_taken:.2f} SECONDS\n")

        return None


    def make_soup_from_url(self, url: str, **kwargs: Any):
        """
        Similar to `make_soup` but a url can be provided instead of markup. 
        The function will get the url's markup and make a BeautifulSoup with it.

        Returns BeautifulSoup if response from url is OK else returns None.

        Args::
            url (str): url from which soup will be created
        """
        response = self._make_request(url)
        if response:
            return self.make_soup(response.content, **kwargs)
        return None

    
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

        urls = list(filter(lambda url: isinstance(url, dict) and any(url), urls))

        if len(urls) < 1:
            raise ValueError("No valid url was found in `urls`")

        results = []
        params = {'save_to': save_to, 'check_ext': check_ext, 'unique_if_query_params': unique_if_query_params}
        urls_download_params = map(lambda dict: {**params, **dict}, urls)

        if fast_download and len(urls) <= 200:
            self.log("FAST DOWNLOAD STARTED...\n")
            with ThreadPoolExecutor() as executor:
                values = executor.map(lambda kwargs: self.download_url(**kwargs), urls_download_params)
            results.extend(values)
            return results

        elif fast_download and len(urls) > 200:
            self.logger.log_warning("CANNOT USE FAST DOWNLOAD! TOO MANY URLS. FALLING BACK TO NORMAL DOWNLOAD.\n")

        self.log("DOWNLOADS STARTED...")
        values = map(lambda kwargs: self.download_url(**kwargs), urls_download_params)
        results.extend(values)

        if results:
            self.log("DOWNLOADS FINISHED!\n")
        else:
            self.log("NOTHING DOWNLOADED!\n")
        return results


    def save_results(self, result: Iterable[str], path: str, **kwargs):
        '''
        Saves a list of results to the given path inside the base storage directory

        Args::
            * result (Iterable[str]): An iterable containing strings to be saved.
            * path (str): path to directory where the file containing `result` will be saved in the base storage directory.
            * **kwargs (Dict | optional): optional parameters to be used when necessary

                    :param `csv_head` (str): heading for csv file type
        '''
        path = os.path.join(self.base_storage_dir, path)
        file_handler = FileHandler(path)  
        if file_handler.filetype == 'csv':
            csv_head = kwargs.get('csv_head', "results").upper()
            url_lists = utils.slice_iterable(result, 1)
            detailed_url_list = [('S/N', csv_head)]
            detailed_url_list.extend([ (c + 1, url_lists[c][0]) for c in range(len(url_lists)) ])
            return file_handler.write_to_file(detailed_url_list)
        return file_handler.write_to_file(result)


    def get_all(self, url: str, target: str, attrs: Dict[str, str] | Iterable[Dict[str, str]] = {}, 
                        count: int = None, recursive: bool = True, **kwargs):
        """
        Parses out the link to all elements with the target name in specified url.

        Returns a list of the links.

        Args::
            * url (str): url of page to be parsed and scanned for target element.
            * target (str): name of HTML element (with a url related attribute).
            * attrs (Dict[str, str] | Iterable[Dict[str, str]]): A dictionary or list of dictionaries of filters on attribute values.
            * count (int): Number of links to be found before stopping.
            * recursive (bool): Performs a recursive search of url page's children
            * **kwargs (Dict | optional): optional parameters to be used for 
                    * creating BeautifulSoup and is going to be passed to the BeautifulSoup class on instantiation.
        """
        self.set_base_url(url)
        response = self._make_request(url)
        urls = []
        if response:
            soup = self.make_soup(response.content, **kwargs)
            elements = []
            url_rel_attr = self._get_element_src_by_tag_name(target)
            if isinstance(attrs, Iterable) and not isinstance(attrs, dict):
                for attr in attrs:
                    elements.extend(soup.find_all(target, attr, recursive=recursive, limit=count))
            else:
                elements.extend(soup.find_all(target, attrs, recursive=recursive, limit=count))
            elements = filter(lambda el: bool(el.get(url_rel_attr)), elements)
            with ThreadPoolExecutor() as executor:
                results = executor.map(lambda arg: self._get_soup_tag(*arg), map(lambda el: (el, False), elements))
                urls.extend(results)
        return urls
            
    
    def get_links(self, url: str, save_to_file: bool = False, file_path: str = "links.csv", **kwargs) -> List[str]:
        """
        Gets all the links from the given url.

        Returns a list of links and saves the links to a file if `save_to_file` is set to True.

        Args:
            * url (str): Url to get the links from.
            * save_to_file (bool, optional): Whether to save the links to a file. Defaults to False.
            * file_path (str, optional): File to save the links to. Defaults to "self.base_storage_dir/links.txt".
            Available file formats are: csv, txt, doc, docx, pdf...
            * **kwargs (Dict | optional): optional parameters to be used for 
                    * creating BeautifulSoup and is going to be passed to the BeautifulSoup class on instantiation.
                    * saving results and is passed to the `save_results` function if `save_to_file` is True.
        """
        result = self.get_all(url, target='a', **kwargs)
        if result and save_to_file is True:
            self.save_results(result, file_path, **kwargs)
        return result


    def get_styles(self, url: str, save_to_file: bool = False, file_path: str = "styles.csv", **kwargs) -> List[str]:
        """
        Gets all the style links from the given url.

        Returns a list of style links and saves the links to a file if `save_to_file` is set to True.

        Args:
            * url (str): Url to get the styles from.
            * save_to_file (bool, optional): Whether to save the styles to a file. Defaults to False.
            * file_path (str, optional): File to save the links to. Defaults to "self.base_storage_dir/styles.txt".
            Available file formats include: csv, txt, doc, docx, pdf...
            * **kwargs (Dict | optional): optional parameters to be used for 
                    * creating BeautifulSoup and is going to be passed to the BeautifulSoup class on instantiation.
                    * saving results and is passed to the `save_results` function if `save_to_file` is True.
        """
        attrs = (
            {'rel': 'stylesheet'},
            {'type': 'text/css'}
        )
        result = self.get_all(url, target='link', attrs=attrs, **kwargs)
        if result and save_to_file is True:
            self.save_results(result, file_path, **kwargs)
        return result
            

    def get_scripts(self, url: str, save_to_file: bool = False, file_path: str = "scripts.csv", **kwargs) -> List[str]:
        """
        Gets all the script links from the given url.

        Returns a list of script links and saves the links to a file if `save_to_file` is set to True.

        Args:
            * url (str): Url to get the scripts from.
            * save_to_file (bool, optional): Whether to save the scripts to a file. Defaults to False.
            * file_path (str, optional): File to save the links to. Defaults to "self.base_storage_dir/scripts.txt".
            Available file formats include: csv, txt, doc, docx, pdf...
            * **kwargs (Dict | optional): optional parameters to be used for 
                    * creating BeautifulSoup and is going to be passed to the BeautifulSoup class on instantiation.
                    * saving results and is passed to the `save_results` function if `save_to_file` is True.
        """
        result = self.get_all(url, target='script', **kwargs)
        if result and save_to_file is True:
            self.save_results(result, file_path, **kwargs)
        return result

    
    def get_fonts(self, url: str, save_to_file: bool = False, file_path: str = "fonts.csv", **kwargs) -> List[str]:
        """
        Gets all the font links from the given url.

        Returns a list of font link and saves the links to a file if `save_to_file` is set to True.

        Args:
            * url (str): Url to get the fonts from.
            * save_to_file (bool, optional): Whether to save the fonts to a file. Defaults to False.
            * file_path (str, optional): File to save the links to. Defaults to "self.base_storage_dir/fonts.txt".
            Available file formats include: csv, txt, doc, docx, pdf...
            * **kwargs (Dict | optional): optional parameters to be used for 
                    * creating BeautifulSoup and is going to be passed to the BeautifulSoup class on instantiation.
                    * saving results and is passed to the `save_results` function if `save_to_file` is True.
        """
        attrs = (
            {'rel': 'preload'},
            {'as': 'font'}
        )
        result = self.get_all(url, target='link', attrs=attrs, **kwargs)
        if result and save_to_file is True:
            self.save_results(result, file_path, **kwargs)
        return result

    
    def get_images(self, url: str, save_to_file: bool = False, file_path: str = "images.csv", **kwargs) -> List[str]:
        """
        Gets all the image links from the given url.

        Returns a list of image links and saves the links to a file if `save_to_file` is set to True.

        Args:
            * url (str): Url to get the images from.
            * save_to_file (bool, optional): Whether to save the images to a file. Defaults to False.
            * file_path (str, optional): File to save the links to. Defaults to "self.base_storage_dir/images.txt".
            Available file formats include: csv, txt, doc, docx, pdf...
            * **kwargs (Dict | optional): optional parameters to be used for 
                    * creating BeautifulSoup and is going to be passed to the BeautifulSoup class on instantiation.
                    * saving results and is passed to the `save_results` function if `save_to_file` is True.
        """
        result = self.get_all(url, target='img', **kwargs)
        if result and save_to_file is True:
            self.save_results(result, file_path, **kwargs)
        return result


    def get_videos(self, url: str, save_to_file: bool = False, file_path: str = "videos.csv", **kwargs) -> List[str]:
        """
        Gets all the video links from the given url.

        Returns a list of video links and saves the links to a file if `save_to_file` is set to True.

        Args:
            - url (str): Url to get the videos from.
            - save_to_file (bool, optional): Whether to save the videos to a file. Defaults to False.
            - file_path (str, optional): File to save the links to. Defaults to "self.base_storage_dir/videos.txt".
            Available file formats include: csv, txt, doc, docx, pdf...
            - **kwargs (Dict | optional): optional parameters to be used when and where necessary

                    :param `csv_head` (str): heading for csv file type when saving results.
        """
        result = self.get_all(url, target='video', **kwargs)
        if result and save_to_file is True:
            self.save_results(result, file_path, **kwargs)
        return result


    def get_audios(self, url: str, save_to_file: bool = False, file_path: str = "audios.csv", **kwargs) -> List[str]:
        '''
        Gets all the audio links from the given url.

        Returns a list of audio links and saves the links to a file if `save_to_file` is set to True.

        Args:
            * url (str): Url to get the audios from.
            * save_to_file (bool, optional): Whether to save the audios to a file. Defaults to False.
            * file_path (str, optional): File to save the links to. Defaults to "self.base_storage_dir/audios.txt".
            Available file formats include: csv, txt, doc, docx, pdf...
            * **kwargs (Dict | optional): optional parameters to be used for 
                    * creating BeautifulSoup and is going to be passed to the BeautifulSoup class on instantiation.
                    * saving results and is passed to the `save_results` function if `save_to_file` is True.ading for csv file type when saving results.
        '''
        result = self.get_all(url, target='audio', **kwargs)
        if result and save_to_file is True:
            self.save_results(result, file_path, **kwargs)
        return result
        

if __name__ == "__main__":
    print(BS4WebScraper.__doc__)