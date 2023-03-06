__version__ = '0.0.1'
__author__ = 'tioluwa'
__all__ = ['BS4WebScraper', 'utils', 'help']
__doc__ = 'A web scraper that uses BeautifulSoup4 to scrape web pages and can translates them to other languages.'
__license__ = 'MIT'
__title__ = 'bs4_web_scraper'
__url__ = 'https://github.com/ti-oluwa/bs4_web_scraper'
__description__ = 'A web scraper that uses BeautifulSoup4 to scrape web pages and can translates them to other languages.'
__keywords__ = 'web scraper, bs4, beautifulsoup4, web scraping, web scraping with python, web scraping with bs4, web scraping with beautifulsoup4, web scraping with translation, web scraping with translation to other languages, web scraping with translation to other languages with python, web scraping with translation to other languages with bs4, web scraping with translation to other languages with beautifulsoup4, web scraping with translation to other languages with python and bs4, web scraping with translation to other languages with python and beautifulsoup4,'
__maintainer__ = 'tioluwa'
__maintainer_email__ = 'tioluwa.dev@gmail.com'
__requires__ = ['beautifulsoup4', 'requests', 'translators', 'lxml', 'html5lib', 'urllib3', 'pytz', 'soupsieve']


from bs4_web_scraper.scripts.scraper import BS4WebScraper
from bs4_web_scraper.scripts import utils, help



