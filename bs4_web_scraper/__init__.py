"""
### A web scraper that uses BeautifulSoup4 to scrape web pages and can translate scraped to other languages.

This module contains the following classes: ::
    - `BS4WebScraper`: Used to create web scraper instances.
    - `Translator`: Used to creates instances used to translate text and html to other languages.
    - `Logger`: Used to creates instances used to log messages to a file.
    - `RequestLimitSetting`: Used to creates instances that is used to limit request frequency for the scraper.
    - `FileHandler`: Used for basic file handling operations, reading and writing into supported file types.

@Author: Daniel T. Afolayan (ti-oluwa.github.io)

### Scrape responsibly and Do not send high frequency requests.

MIT License
------------
Copyright (c) 2023 ti_oluwa

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

__version__ = '0.2.0'
__date__ = '20-09-2023'
__author__ = 'Daniel T. Afolayan'
__license__ = 'MIT'
__title__ = 'bs4_web_scraper'
__url__ = 'https://github.com/ti-oluwa/bs4_web_scraper'
__maintainer__ = 'ti-oluwa'
__maintainer_email__ = 'tioluwa.dev@gmail.com'
__requires__ = [
    'beautifulsoup4', 'requests', 'translators', 'lxml', 
    'html5lib', 'urllib3', 'pytz', 'soupsieve', 'pyyaml',
    'toml',
]

from .exceptions import *

credentials_template = {
    'auth_url': '<Login URL>',
    'auth_username_field': '<Username Field>',
    'auth_password_field': '<Password Field>',
    'auth_username': '<Username>',
    'auth_password': '<Password>',
    'additional_auth_fields': {
        '<Field Name>': '<Field Value>',
    },
}


# NOTE: 
# 'rra' means 'resource-related-attribute'
# A 'resource-related-attribute' in this case refers to any HTML tag attribute that points to a resource. Examples of
# resource-related-attributes include; 'href'(of the <link> tag) and 'src'(of the <img> tag).
