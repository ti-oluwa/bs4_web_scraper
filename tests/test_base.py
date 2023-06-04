import unittest
from bs4 import BeautifulSoup
import requests
import os
import copy
from urllib3.util.url import parse_url
import warnings
import random

from bs4_web_scraper.base import BS4BaseScraper
from bs4_web_scraper.file_handler import FileHandler
from bs4_web_scraper.translate import Translator

credentials = {
    'auth_url': 'https://edenplace.pythonanywhere.com/signin/',
    'auth_username_field': 'user_id',
    'auth_password_field': 'password',
    'auth_username': 'Tioluwa',
    'auth_password': 'toltom',
}

urls = [
    'http://speedtest.ftp.otenet.gr/files/test100k.db',
    {
        'url': 'http://speedtest.ftp.otenet.gr/files/test100k.db',
        'save_as': 'test.db',
    },
    {
        'url': 'http://speedtest.ftp.otenet.gr/files/test100k.db',
        'save_to': 'test'
    }
]


class BaseTestClassForBS4Scraper(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scraper = BS4BaseScraper(base_storage_dir='./tests/results')
        cls.url = 'https://edenplace.pythonanywhere.com/events/publish'
        cls.markup_filepath = os.path.abspath('./tests/fixtures/index.html')
        cls.markup_file = open(cls.markup_filepath, 'r+')
        cls.markup = cls.markup_file.read()
        cls.auth_credentials = credentials
        # warnings.filterwarnings(action="ignore", message='unclosed', category=ResourceWarning)

    @classmethod
    def tearDownClass(self):
        self.scraper.reset()
        self.markup_file.close()


class TestBS4BaseScraper(BaseTestClassForBS4Scraper):
    
    def test_get(self):
        response  = self.scraper.get(self.url)
        if response:
            self.assertIsInstance(response, requests.Response)
    
    def test_get_base_url(self):
        base_url = self.scraper.get_base_url(self.url)
        self.assertIsInstance(base_url, str)
    
    def test_set_base_url(self):
        self.scraper.set_base_url(self.url)
        self.assertIsInstance(self.scraper.base_url, str)

    def set_scraper_base_url(self):
        return self.scraper.set_base_url(self.url)
    
    def test_get_actual_url_from_rra(self):
        self.set_scraper_base_url()
        actual_url = self.scraper.get_actual_url_from_rra('/signout/')
        actual_url_obj = parse_url(actual_url)
        self.assertIsInstance(actual_url, str)
        self.assertIsNotNone(actual_url_obj.scheme)
        self.assertIsNotNone(actual_url_obj.netloc)
        self.assertIsNotNone(actual_url_obj.path)

    def test_get_rra_by_tag_name(self):
        rra1 = self.scraper.get_rra_by_tag_name('a')
        rra2 = self.scraper.get_rra_by_tag_name('h1')
        self.assertIsInstance(rra1, str)
        self.assertIsNone(rra2)

    def test_make_soup(self):
        str_soup = self.scraper.make_soup(self.markup)
        file_soup = self.scraper.make_soup(self.markup_file)
        self.assertIsInstance(str_soup, BeautifulSoup)
        self.assertIsInstance(file_soup, BeautifulSoup)

    def test_make_soup_from_url(self):
        soup = self.scraper.make_soup_from_url(self.url)
        self.assertIsInstance(soup, BeautifulSoup)
    
    def test_get_tag_rra(self):
        soup = self.scraper.make_soup(markup=self.markup)
        img_tag = soup.find('img')
        result1 = self.scraper.get_tag_rra(img_tag, download=False)
        result2 = self.scraper.get_tag_rra(img_tag, download=True)
        self.assertTrue(isinstance(result1, (str, None)))
        self.assertTrue(isinstance(result2, (FileHandler, None)))

    def test_get_request_headers(self):
        self.set_scraper_base_url()
        headers = self.scraper.get_request_headers()
        self.assertEqual(headers['origin'], self.scraper.base_url)
        self.assertIsInstance(headers['User-Agent'], str)

    def test_authenticate(self):
        try:
            self.scraper.authenticate(self.auth_credentials)
        except Exception as e:
            self.fail(e.__str__())

    def test_get_associated_files_and_return_soup(self):
        file_hdl = FileHandler(self.markup_filepath, exists_ok=True, allow_any=True)
        soup1 = self.scraper.get_associated_files_and_return_soup(file_hdl)
        self.assertIsInstance(soup1, BeautifulSoup)
        soup2 = self.scraper.make_soup(self.markup)
        style1 = soup1.find('link', attrs={'rel': 'stylesheet'}).get('href', None)
        style2 = soup2.find('link', attrs={'rel': 'stylesheet'}).get('href', None)
        if style1 and style2:
            self.assertNotEqual(style1, style2)

    def test_save_to_file(self):
        file_hdl1 = self.scraper.save_to_file('main.html', storage_path='/test_files/', content=self.markup, mode='w')
        if file_hdl1:
            expected_path = os.path.abspath('./tests/results/test_files/main.html')
            self.assertEqual(file_hdl1.filepath, expected_path)
            self.assertIsInstance(file_hdl1, FileHandler)
            # file_hdl1.delete_file()
        file_hdl2 = self.scraper.save_to_file(filename='index.html', 
                                                storage_path=os.path.abspath(self.markup_filepath), 
                                                content=self.markup, mode='w')
        if file_hdl2:
            expected_path = os.path.abspath(self.markup_filepath)
            self.assertEqual(file_hdl2.filepath, expected_path)
            self.assertIsInstance(file_hdl2, FileHandler)
            if file_hdl2.created_file:
                file_hdl2.delete_file()
        
    def test_parse_storage_path_from_Url(self):
        path = self.scraper.parse_storage_path_from_Url(parse_url(self.url))
        self.assertIsInstance(path, str)
        
    def test_set_translator(self):
        try:
            self.scraper.set_translator("bing")
            self.assertIsInstance(self.scraper.translator, Translator)
        except Exception as e:
            self.fail(e.__str__())

    def test_authenticate(self):
        try:
            self.scraper.authenticate(self.auth_credentials)
            self.assertIsInstance(self.scraper.is_authenticated, bool)
            self.assertTrue(self.scraper.is_authenticated)
        except Exception as e:
            self.fail(e.__str__())

    def test_get_link_tag(self):
        soup = self.scraper.make_soup(self.markup)
        link_tag = random.choice(soup.find_all('a'))

        # get actual url from link tag's rra
        actual_url = self.scraper.get_link_tag(link_tag, download=False)
        if actual_url:
            self.assertIsInstance(actual_url, str)
            url_obj = parse_url(actual_url)
            self.assertIsNotNone(url_obj.scheme)
            self.assertIsNotNone(url_obj.netloc)

        # get file handler from link tag's rra
        file_hdl = self.scraper.get_link_tag(link_tag, download=True)
        if file_hdl:
            self.assertIsInstance(file_hdl, FileHandler)
    
    def test_log(self):
        try:
            self.scraper.log("Test Log")
        except Exception as e:
            self.fail(e.__str__())

    def test__scrape(self):
        try:
            self.set_scraper_base_url()
            self.scraper._scrape(url=self.scraper.base_url, scrape_depth=0, translate_to='fr')
            self.scraper.translate_to = None
            self.scraper._scrape(url=self.scraper.base_url, scrape_depth=2)
        except Exception as e:
            self.fail(e.__str__())

    def test_set_auth_credentials(self):
        try:
            self.scraper.set_auth_credentials(self.auth_credentials)
        except Exception as e:
            self.fail(e.__str__())

    def test_close_session(self):
        previous_session = copy.deepcopy(self.scraper.session)
        self.scraper.close_session()
        self.assertNotEqual(previous_session, self.scraper.session)

    def test_renew_session(self):
        previous_session = copy.deepcopy(self.scraper.session)
        self.scraper.renew_session()
        self.assertNotEqual(previous_session, self.scraper.session)

    def test_download_url(self):
        self.set_scraper_base_url()
        # normal download
        downloaded_file_hdl = self.scraper.download_url(urls[0])
        self.assertIsInstance(downloaded_file_hdl, FileHandler)
        self.assertTrue(os.path.exists(downloaded_file_hdl.filepath))

        # download with save_as and save_to
        downloaded_file_hdl = self.scraper.download_url(urls[0], save_as='test.db', save_to=os.path.abspath('./tests/results/test_files/'))
        self.assertTrue(os.path.exists(downloaded_file_hdl.filepath))
        self.assertTrue(downloaded_file_hdl.filename == 'test.db')

        # download and save with file name that does not match the file extension in the url with check_ext = True
        with self.assertRaises(ValueError):
            downloaded_file_hdl = self.scraper.download_url(urls[0], save_as='test.md', save_to=os.path.abspath('./tests/results/test_files/'), check_ext=True)
        
        # download and save with file name that does not match the file extension in the url with check_ext = False
        downloaded_file_hdl = self.scraper.download_url(urls[0], save_as='test.md', save_to=os.path.abspath('./tests/results/test_files/'), check_ext=False)
        self.assertTrue(os.path.exists(downloaded_file_hdl.filepath))

        # download file with no extension and with no save_as provided
        with self.assertRaises(ValueError):
            downloaded_file_hdl = self.scraper.download_url(self.url, save_to=os.path.abspath('./tests/results/test_files/'))
        
        # download file with no extension and with save_as provided
        downloaded_file_hdl = self.scraper.download_url(self.url, save_as='test.html', save_to=os.path.abspath('./tests/results/test_files/'), check_ext=False)
        self.assertTrue(os.path.exists(downloaded_file_hdl.filepath))
        
        # download file that already exists
        downloaded_file_hdl = self.scraper.download_url(urls[0], save_to=os.path.abspath('./tests/results/test_files/'))
        self.assertIsInstance(downloaded_file_hdl, FileHandler)



if "__name__" == "__main__":
    unittest.main()

# RUN WITH 'python -m unittest discover tests "test_*.py"' from project directory