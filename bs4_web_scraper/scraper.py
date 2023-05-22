"""
DESCRIPTION: ::
    This module contains the BS4WebScraper class which is the base class for creating scraper instances 
    used to scrape websites.

    Don't make high frequency requests! Scrape responsibly!
    If you are using this module to scrape websites for commercial purposes, please consider supporting the
    websites you are scraping by making a donation.
"""
import os
import re
from typing import (AnyStr, Dict, List, Tuple)
from collections.abc import Iterable
import time
from concurrent.futures import ThreadPoolExecutor
from urllib3.util.url import parse_url

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
            self.log(f"SCRAPING COMPLETED IN {(time_taken / 60):.2f} MINUTE{'S'[:round(time_taken / 60)^1]}\n")
        else:
            self.log(f"SCRAPING COMPLETED IN {time_taken:.2f} SECOND{'S'[:round(time_taken)^1]}\n")

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
        Saves a list of results to the file in the given path inside the base storage directory

        Args::
            * result (Iterable[str]): An iterable containing strings to be saved.
            * path (str): path to directory where the file containing `result` will be saved in the base storage directory.
            If it is an absolute path, the file will be saved in the specified path.
            * **kwargs (Dict | optional): optional parameters to be used when necessary
                    * `csv_head` (str): heading for csv file type
        '''
        path = os.path.join(self.base_storage_dir, path)
        file_handler = FileHandler(path)  
        if file_handler.filetype == 'csv':
            csv_head = kwargs.get('csv_head', "results").upper()
            url_lists = utils.slice_iterable(result, 1)
            detailed_url_list = [('S/N', csv_head)]
            detailed_url_list.extend([ (c + 1, url_lists[c][0]) for c in range(len(url_lists)) ])
            return file_handler.write_to_file(detailed_url_list)
        for r in result: 
            file_handler.write_to_file(f'{r}\n') 
        return None


    def find_all(self, url: str, target: str, attrs: Dict[str, str] | Iterable[Dict[str, str]] = {}, 
                        depth: int = 0, count: int = None, recursive: bool = True):
        """
        Parses out the url/links on all elements with the target name in specified url.
        NOTE: This only works for elements with a resource(url) related attribute. To get HTML elements with no resource related attribute, use `find_all_tags`.

        Removes duplicates and returns a list of the links/urls.

        Args::
            * url (str): url of page to be parsed and scanned for target element.
            * target (str): name of HTML element (with a url related attribute).
            * attrs (Dict[str, str] | Iterable[Dict[str, str]]): A dictionary or list of dictionaries of filters on attribute values.
            * depth (int): Number of levels to recursively search for target items. Defaults to 0.
            * count (int): Number of target items to be found on a url page before stopping.
            * recursive (bool): Performs a recursive search of url page's children
        """
        self.set_base_url(url)
        base_url_obj = parse_url(self.base_url)
        urls = []
        soup = self.make_soup_from_url(url)
        if soup is not None:
            tags = []
            rra = self.get_rra_by_tag_name(target)
            if isinstance(attrs, Iterable) and not isinstance(attrs, dict):
                for attr in attrs:
                    tags.extend(soup.find_all(target, attr, recursive=recursive, limit=count))
            else:
                tags.extend(soup.find_all(target, attrs, recursive=recursive, limit=count))

            tags = filter(lambda tag: bool(tag.get(rra)), tags)
            with ThreadPoolExecutor() as executor:
                results = executor.map(lambda args: self.get_tag_rra(*args), map(lambda tag: (tag, False), tags))
                urls.extend(results)

            while depth > 0:
                depth -= 1
                link_tags = soup.find_all('a', recursive=recursive)
                links = [ self.get_link_tag(link_tag, download=False) for link_tag in link_tags ]
                links = filter(lambda link: bool(link), links)   
                link_objs = [ (link, parse_url(link)) for link in links ]
                links = [ link_obj[0] for link_obj in link_objs if (base_url_obj.netloc and link_obj[1].netloc) and (base_url_obj.netloc in link_obj[1].netloc) ] 

                with ThreadPoolExecutor() as executor:
                    results = executor.map(lambda args: self.find_all(*args), map(lambda link: (link, target, attrs, depth, count, recursive), links))
                    for result in results:
                        if result:
                            urls.extend(result)
                continue
        urls = list(set(urls))
        return urls
    

    def find_all_tags(self, url: str, target: str, attrs: Dict[str, str] | Iterable[Dict[str, str]] = {},
                        depth: int = 0, count: int = None, recursive: bool = True):
        """
        Gets all HTML elements with the target name in specified url.

        Returns a list of the HTML elements with the target name as bs4.element.Tag objects.

        Args::
            * url (str): url of page to be parsed and scanned for target element.
            * target (str): name of HTML element (with a url related attribute).
            * attrs (Dict[str, str] | Iterable[Dict[str, str]]): A dictionary or list of dictionaries of filters on attribute values.
            * depth (int): Number of levels to recursively search for target items. Defaults to 0.
            * count (int): Number of target items to be found on a url page before stopping.
            * recursive (bool): Performs a recursive search of url page's children
        """
        self.set_base_url(url)
        base_url_obj = parse_url(self.base_url)
        soup = self.make_soup_from_url(url)
        if soup is not None:
            tags = []
            if isinstance(attrs, Iterable) and not isinstance(attrs, dict):
                for attr in attrs:
                    tags.extend(soup.find_all(target, attr, recursive=recursive, limit=count))
            else:
                tags.extend(soup.find_all(target, attrs, recursive=recursive, limit=count))

            while depth > 0:
                depth -= 1
                link_tags = soup.find_all('a', recursive=recursive)
                links = [ self.get_link_tag(link_tag, download=False) for link_tag in link_tags ]
                links = filter(lambda link: bool(link), links)   
                link_objs = [ (link, parse_url(link)) for link in links ]
                links = [ link_obj[0] for link_obj in link_objs if (base_url_obj.netloc and link_obj[1].netloc) and (base_url_obj.netloc in link_obj[1].netloc) ] 

                with ThreadPoolExecutor() as executor:
                    results = executor.map(lambda args: self.find_all_tags(*args), map(lambda link: (link, target, attrs, depth, count, recursive), links))
                    for result in results:
                        if result:
                            tags.extend(result)
                continue
        return tags

    
    def find_links(self, url: str, depth: int = 0, save_to_file: bool = False, file_path: str = "links.csv", **kwargs) -> List[str]:
        """
        Gets all the links from the given url.

        Removes duplicates and returns a list of links and saves the links to a file if `save_to_file` is set to True.

        Args:
            * url (str): Url to get the links from.
            * depth (int, optional): Number of levels to recursively search for links. Defaults to 0.
            * save_to_file (bool, optional): Whether to save the links to a file. Defaults to False.
            * file_path (str, optional): File to save the links to. Defaults to "self.base_storage_dir/links.txt".
            If it is an absolute path, the file will be saved in the specified path.
            Available file formats are: csv, txt, doc, docx, pdf...
            * **kwargs (Dict | optional): optional parameters to be used for 
                    * `csv_head` (str): saving results and is passed to the `save_results` function if `save_to_file` is True.
        """
        result = self.find_all(url, target='a', depth=depth)
        if result and save_to_file is True:
            kwargs['csv_head'] = kwargs.get('csv_head', 'Links')
            self.save_results(result, file_path, **kwargs)
        return result


    def find_stylesheets(self, url: str, depth: int = 0, save_to_file: bool = False, file_path: str = "styles.csv", **kwargs) -> List[str]:
        """
        Gets all the stylesheet links from the given url.

        Removes duplicates and returns a list of style links and saves the links to a file if `save_to_file` is set to True.

        Args:
            * url (str): Url to get the styles from.
            * depth (int, optional): Number of levels to recursively search for stylesheet links. Defaults to 0.
            * save_to_file (bool, optional): Whether to save the styles to a file. Defaults to False.
            * file_path (str, optional): File to save the links to. Defaults to "self.base_storage_dir/styles.txt".
            If it is an absolute path, the file will be saved in the specified path.
            Available file formats include: csv, txt, doc, docx, pdf...
            * **kwargs (Dict | optional): optional parameters to be used for 
                    * `csv_head` (str): saving results and is passed to the `save_results` function if `save_to_file` is True.
        """
        attrs = (
            {'rel': 'stylesheet'},
            {'type': 'text/css'}
        )
        result = self.find_all(url, target='link', attrs=attrs, depth=depth)
        if result and save_to_file is True:
            kwargs['csv_head'] = kwargs.get('csv_head', 'Stylesheets')
            self.save_results(result, file_path, **kwargs)
        return result
            

    def find_scripts(self, url: str, depth: int = 0, save_to_file: bool = False, file_path: str = "scripts.csv", **kwargs) -> List[str]:
        """
        Gets all the script links from the given url.

        Removes duplicates and returns a list of script links and saves the links to a file if `save_to_file` is set to True.

        Args:
            * `url` (str): Url to get the scripts from.
            * `depth` (int, optional): Number of levels to recursively search for script links. Defaults to 0.
            * `save_to_file` (bool, optional): Whether to save the scripts to a file. Defaults to False.
            * `file_path` (str, optional): File to save the links to. Defaults to "self.base_storage_dir/scripts.txt".
            If it is an absolute path, the file will be saved in the specified path.
            Available file formats include: csv, txt, doc, docx, pdf...
            * `**kwargs` (Dict | optional): optional parameters to be used for 
                    * `csv_head` (str): saving results and is passed to the `save_results` function if `save_to_file` is True.
        """
        result = self.find_all(url, target='script', depth=depth)
        if result and save_to_file is True:
            kwargs['csv_head'] = kwargs.get('csv_head', 'Scripts')
            self.save_results(result, file_path, **kwargs)
        return result

    
    def find_fonts(self, url: str, depth: int = 0, save_to_file: bool = False, file_path: str = "fonts.csv", **kwargs) -> List[str]:
        """
        Gets all the font links from the given url.

        Removes duplicates and returns a list of font link and saves the links to a file if `save_to_file` is set to True.

        Args:
            * url (str): Url to get the fonts from.
            * depth (int, optional): Number of levels to recursively search for font links. Defaults to 0.
            * save_to_file (bool, optional): Whether to save the fonts to a file. Defaults to False.
            * file_path (str, optional): File to save the links to. Defaults to "self.base_storage_dir/fonts.txt".
            If it is an absolute path, the file will be saved in the specified path.
            Available file formats include: csv, txt, doc, docx, pdf...
            * **kwargs (Dict | optional): optional parameters to be used for 
                    * `csv_head` (str): saving results and is passed to the `save_results` function if `save_to_file` is True.
        """
        attrs = (
            {'rel': 'preload'},
            {'as': 'font'}
        )
        result = self.find_all(url, target='link', attrs=attrs, depth=depth)
        if result and save_to_file is True:
            kwargs['csv_head'] = kwargs.get('csv_head', 'Font Links')
            self.save_results(result, file_path, **kwargs)
        return result

    
    def find_images(self, url: str, depth: int = 0, save_to_file: bool = False, file_path: str = "images.csv", **kwargs) -> List[str]:
        """
        Gets all the image links from the given url.

        Removes duplicates and returns a list of image links and saves the links to a file if `save_to_file` is set to True.

        Args:
            * url (str): Url to get the images from.
            * depth (int, optional): Number of levels to recursively search for image links. Defaults to 0.
            * save_to_file (bool, optional): Whether to save the images to a file. Defaults to False.
            * file_path (str, optional): File to save the links to. Defaults to "self.base_storage_dir/images.txt".
            If it is an absolute path, the file will be saved in the specified path.
            Available file formats include: csv, txt, doc, docx, pdf...
            * **kwargs (Dict | optional): optional parameters to be used for 
                    * `csv_head` (str): saving results and is passed to the `save_results` function if `save_to_file` is True.
        """
        result = self.find_all(url, target='img', depth=depth)
        if result and save_to_file is True:
            kwargs['csv_head'] = kwargs.get('csv_head', 'Image Links')
            self.save_results(result, file_path, **kwargs)
        return result


    def find_videos(self, url: str, depth: int = 0, save_to_file: bool = False, file_path: str = "videos.csv", **kwargs) -> List[str]:
        """
        Gets all the video links from the given url.

        Removes duplicates and returns a list of video links and saves the links to a file if `save_to_file` is set to True.

        Args:
            * url (str): Url to get the videos from.
            * depth (int, optional): Number of levels to recursively search for video links. Defaults to 0.
            * save_to_file (bool, optional): Whether to save the videos to a file. Defaults to False.
            * file_path (str, optional): File to save the links to. Defaults to "self.base_storage_dir/videos.txt".
            If it is an absolute path, the file will be saved in the specified path.
            Available file formats include: csv, txt, doc, docx, pdf...
            * **kwargs (Dict | optional): optional parameters to be used when and where necessary
                    * `csv_head` (str): saving results and is passed to the `save_results` function if `save_to_file` is True.
        """
        video_types = ('video/mp4', 'video/mpeg', 'video/ogg', 'video/webm', 'video/3gpp', 'video/quicktime')
        v_list = [ {'type': v} for v in video_types ]
        result = self.find_all(url, target='source', attrs=v_list, depth=depth)
        if result and save_to_file is True:
            kwargs['csv_head'] = kwargs.get('csv_head', 'Video Links')
            self.save_results(result, file_path, **kwargs)
        return result


    def find_audios(self, url: str, depth: int = 0, save_to_file: bool = False, file_path: str = "audios.csv", **kwargs) -> List[str]:
        '''
        Gets all the audio links from the given url.

        Removes duplicates and returns a list of audio links and saves the links to a file if `save_to_file` is set to True.

        Args:
            * url (str): Url to get the audios from.
            * depth (int, optional): Number of levels to recursively search for audio links. Defaults to 0.
            * save_to_file (bool, optional): Whether to save the audios to a file. Defaults to False.
            * file_path (str, optional): File to save the links to. Defaults to "self.base_storage_dir/audios.txt".
            If it is an absolute path, the file will be saved in the specified path.
            Available file formats include: csv, txt, doc, docx, pdf...
            * **kwargs (Dict | optional): optional parameters to be used for 
                    * `csv_head` (str): saving results and is passed to the `save_results` function if `save_to_file` is True.
        '''
        audio_types = ('audio/mpeg', 'audio/mp3', 'audio/ogg', 'audio/wav', 'audio/aac', 'audio/flac', 'audio/m4a', 'audio/wma')
        a_list = [ {'type': a} for a in audio_types ]
        result = self.find_all(url, target='source', attrs=a_list, depth=depth)
        if result and save_to_file is True:
            kwargs['csv_head'] = kwargs.get('csv_head', 'Audio Links')
            self.save_results(result, file_path, **kwargs)
        return result
        

    def get_emails(self, url: str, depth: int = 0, save_to_file: bool = False, file_path: str = "emails.csv", **kwargs) -> List[str]:
        """
        Searches for and returns a list of emails found in the given url.

        Args:
            * url (str): Url to get the emails from.
            * depth (int, optional): Number of levels to recursively search for emails. Defaults to 0.
            * save_to_file (bool, optional): Whether to save the emails to a file. Defaults to False.
            * file_path (str, optional): File to save the links to. Defaults to "self.base_storage_dir/emails.txt".
            If it is an absolute path, the file will be saved in the specified path.
            Available file formats include: csv, txt, doc, docx, pdf...
            * **kwargs (Dict | optional): optional parameters to be used for
                    * `csv_head` (str): saving results and is passed to the `save_results` function if `save_to_file` is True.
                    * `re_flags` (RegexFlag): adding regex flags and is passed to the `re.compile` function.
        """
        email_re = r'[-|\w]+@\w+.\w{2,}'
        kwargs['re_flags'] = kwargs.get('re_flags', re.IGNORECASE)
        kwargs['csv_head'] = kwargs.get('csv_head', 'Emails')
        return self.find_pattern(url, email_re, depth, save_to_file, file_path, kwargs)


    def find_phone_numbers(self, url: str, depth: int = 0, save_to_file: bool = False, file_path: str = "phones.csv", **kwargs) -> List[Tuple[str, str]]:
        """
        Searches for and returns a list of phone numbers which conform to the E.164 standard found in the given url. 

        Returns a list of phone numbers.

        Args:
            * `url` (str): Url to get the phone numbers from.
            * `depth` (int, optional): Number of levels to recursively search for phone numbers. Defaults to 0.
            * `save_to_file` (bool, optional): Whether to save the phone numbers to a file. Defaults to False.
            * `file_path` (str, optional): File to save the links to. Defaults to "self.base_storage_dir/phones.txt".
            If it is an absolute path, the file will be saved in the specified path.
            Available file formats include: csv, txt, doc, docx, pdf...
            * `**kwargs` (Dict | optional): optional parameters to be used for
                    * `csv_head` (str): saving results and is passed to the `save_results` function if `save_to_file` is True.
                    * `re_flags` (RegexFlag): adding regex flags and is passed to the `re.compile` function.
        """
        pn_re = r'(\+\d{1,3})?[\s-]?(\d{7,16})'
        kwargs['csv_head'] = kwargs.get('csv_head', 'Phone Numbers')
        return self.find_pattern(url, pn_re, depth, save_to_file, file_path, kwargs)


    def find_pattern(self, url: str, regex: str | AnyStr, depth: int = 0, save_to_file: bool = False, file_path: str = "re.csv", kwargs: Dict[str, str] = None) -> List[str]:
        """
        Takes a regex pattern and returns a list of matches found in the given url.

        Args:
            * url (str): Url to get the matches from.
            * regex (str | AnyStr): Regex pattern to search for.
            * depth (int, optional): Number of levels to recursively search for matches. Defaults to 0.
            * save_to_file (bool, optional): Whether to save the matches to a file. Defaults to False.
            * file_path (str, optional): File to save the links to. Defaults to "self.base_storage_dir/re.csv".
            If it is an absolute path, the file will be saved in the specified path.
            Available file formats include: csv, txt, doc, docx, pdf...
            * **kwargs (Dict | optional): optional parameters to be used for
                    * `csv_head` (str): saving results and is passed to the `save_results` function if `save_to_file` is True.
                    * `re_flags` (RegexFlag): adding regex flags and is passed to the `re.compile` function.
        """
        self.set_base_url(url)
        base_url_obj = parse_url(self.base_url)
        pattern = re.compile(regex, flags=kwargs.get('re_flags', re.MULTILINE))
        soup = self.make_soup_from_url(url)
        text = soup.get_text() if soup else ''
        result = list({ match for match in pattern.findall(text) })

        while depth > 0:
            depth -= 1
            link_tags = soup.find_all('a', recursive=True)
            links = [ self.get_link_tag(link_tag, download=False) for link_tag in link_tags ]
            links = filter(lambda link: bool(link), links)
            link_objs = [ (link, parse_url(link)) for link in links ]
            links = [ link_obj[0] for link_obj in link_objs if (base_url_obj.netloc and link_obj[1].netloc) and (base_url_obj.netloc in link_obj[1].netloc) ]

            with ThreadPoolExecutor() as executor:
                results = executor.map(lambda args: self.find_pattern(*args), map(lambda link: (link, regex, depth, save_to_file, file_path, kwargs), links))
                for r in results:
                    if r:
                        result.extend(r)
            continue

        result_ = []
        for r in result:
            if isinstance(r, (list, tuple)):
                r = ''.join(r)
            result_.append(r)

        if result_ and depth == 0 and save_to_file is True:
            kwargs['csv_head'] = kwargs.get('csv_head', 'Matches')
            self.save_results(result_, file_path, **kwargs)
        return result_



if __name__ == "__main__":
    print(BS4WebScraper.__doc__)