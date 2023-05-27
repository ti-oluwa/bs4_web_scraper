## bs4_web_scraper

### __A web scraper based on the BeautifulSoup4 library with translation capabilities.__

[PyPI](https://pypi.org/project/bs4-web-scraper/)


## Dependencies

- Python 3.11
- beautifulsoup4
- translators
- requests
- lxml
- html5lib
- pyyaml
- toml


## Setup Local Development Environment

1. Make sure you have python3 installed on your local machine.
2. Clone the repository to local machine into your project directory.
3. Change directory into the repository "bs4_web_scraper" and `pip install -r requirements.txt`. You're ready to go if the installations were successful.
4. For a quick demo, run `example.py`.


## Installation

1. Make sure you have python3 installed on your local machine.
2. Run `pip install bs4-web-scraper` on terminal.
3. Import the module into your project and you're good to go.


## Features

* Web scraping
* Translation
* Saving scraped data to a file
* Downloading data from a web page or URL
* Logging the scraping process


## Usage

Before using the scraper, make sure you have an internet connection. The scraper uses the internet to scrape web pages and translate scraped data.

**NOTE:**

* The scraper is not a browser. It does not execute JavaScript. It only scrapes the HTML content of web pages.
* The scraper requires an internet connection to scrape web pages and translate scraped data.
* The scraper was built with HTML5 web pages in mind. It may not work well with older HTML versions.
* Some web pages may not be scraped properly due to the way they are structured. This is not a bug. It is a limitation of the scraper.
* The scraper only attempts to authenticate with the information provided. The success of the authentication largely depends on the information provided to the scraper. This is because the authentication process varies from website to website. It is up to the user to provide the correct authentication information.
* The scraper does not support authentication with CAPTCHA.
* The scraper does not support scraping dynamic web pages by default.
* Some methods of the scraper may not work properly if the scraper is not instantiated properly. Ensure to read the docstrings of the methods and class attributes before using them.
* A number of methods of the scraper use multithreading. This means that the scraper can run multiple threads at the same time. This is done to speed up the scraping process. The number of threads used by the scraper can be set by the user but it is advisable to leave it at its default value.

### Importing the module

```python

from bs4_web_scraper.scraper import BS4WebScraper

```

### Creating a scraper object

The following example shows how to instantiate and customize the scraper's settings. The default settings are used if no parameters are passed to the scraper object.

```python

# Here, the scraper object is created with the default settings
bs4_scraper = BS4WebScraper()

# To customize the scraper's settings, pass a dictionary of the preferred instantiation parameters to the scraper object.
params = {
    "parser": "html.parser",
    "markup_filename": "base.html",
    "log_filepath": "./scrape_log/log.txt",
    "no_of_requests_before_pause": 30, # This should not exceed 50 to avoid high frequency requests. The upper limit is 100
    "scrape_session_pause_duration": 20, # pause duration in seconds. It is advisable to leave this at its default, "auto".
    "max_no_of_retries": 5,
    "base_storage_dir": "./scraped_data",
    "storage_path": ".",
    "translation_engine": "bing",
    
}

bs4_scraper = BS4WebScraper(**params)

```

### Instantiation parameters

To read more about the instantiation parameters and class attributes, run the following command:

```python
>>> print(BS4WebScraper.__doc__)

```


### Scraping a web page

Let's say you want to download a website/page to your local machine along with its dependencies(like CSS files, scripts, images or fonts), the `scrape` method can be used. Below is an example of how to scrape a web site.

```python

# Scraping google.com
bs4_scraper.scrape(url="https://www.google.com", scrape_depth=0)

```

In the above example, the `scrape_depth` parameter is set to 0. This means that the scraper will only scrape the web page at the given url. If the `scrape_depth` parameter is set to 1, the scraper will scrape the web page at the given url and all the web pages linked to it. If the `scrape_depth` parameter is set to 2, the scraper will scrape the web page at the given url and all the web pages linked to it and all the web pages linked to the web pages linked to it and so on.



### Translating scraped data

To translate the scraped data, set the `translate_to` parameter to the language you want to translate to. The following example shows how to translate the scraped data to French. The translation is done using the translation engine specified in the instantiation parameters. The default translation engine is "google" (Google Translate). To change the translation engine, set the `translation_engine` parameter or attribute to the preferred translation engine. The following example shows how to translate the scraped data to French using the Bing translation engine.

```python

# Scraping a web page and translating the scraped data to French (during instantiation)
bs4_scraper = BS4WebScraper(..., translation_engine="bing")
# or (after instantiation)
bs4_scraper.translation_engine = "bing"

bs4_scraper.scrape(url="https://www.google.com", scrape_depth=0, translate_to="fr")

```

To get a list of available translation engines you can use, do the following:

```python
from bs4_web_scraper import translate

# INTERNET CONNECTION REQUIRED
print(translate.translation_engines)

```

Translation of the web pages is done immediately after scraping. The `translate_to` parameter is set to "fr" in the above example. This means that the scraped data will be translated to French. The `translate_to` parameter can be set to any of the languages supported by the scraper's translation engine.

To get a list of the languages supported by the scraper's translation engine, do:

```python

print(bs4_scraper.translator.supported_languages)

```


### Scraping web sites or pages that require authentication

To scrape websites or pages that require authentication, you can pass the `credentials` parameter to the `scrape` method.The following example shows how to scrape a web page that requires authentication.

```python

# Scraping a web page that requires authentication
credentials = {
    'auth_url': 'https://www.websitewithauth.com/login_path/',
    'auth_username_field': 'usernamefieldname',
    'auth_password_field': 'passwordfieldname',
    'auth_username': 'yourusername',
    'auth_password': 'yourpassword',
    'additional_auth_fields': {
        'fieldname': 'fieldvalue',
        'fieldname': 'fieldvalue',
    }
}

bs4_scraper.scrape(url="https://www.websitewithauth.com", scrape_depth=0, credentials=credentials)

```

You can also authenticate the scraper before scraping by passing the `credentials` parameter to the `authenticate` method. The following example shows how to authenticate the scraper before scraping.

```python

# Authenticating the scraper before scraping
bs4_scraper.authenticate(credentials=credentials)
bs4_scraper.scrape(url="https://www.websitewithauth.com", scrape_depth=0)

# or in the case of downloading data from a web page that requires authentication
bs4_scraper.authenticate(credentials=credentials)
bs4_scraper.download_url(url="https://www.websitewithauth.com/download/example.mp4", save_as="example.mp4", save_to="downloads")

# run help(bs4_scraper.downloaded_url) for more information on the download_url method

```

NOTE: `credentials` should always take the form of a dictionary with the following keys: `auth_url`, `auth_username_field`, `auth_password_field`, `auth_username`, `auth_password`, `additional_auth_fields`. The `additional_auth_fields` key is optional. It is used to pass additional authentication fields that may be required by the website or page.

To get a quick template for the `credentials` dictionary, do:

```python

import bs4_web_scraper

print(bs4_web_scraper.credentials_template)

```

### Other useful scraper methods

The following are some useful methods for scraping web data using the scraper class.

- `download_url`
- `download_urls`
- `find_all`
- `find_all_tags`
- `find_links`
- `find_stylesheets`
- `find_scripts`
- `find_videos`
- `find_images`
- `find_audios`
- `find_fonts`
- `find_pattern`
- `find_emails`
- `find_phone_numbers`

For information on how to use these methods, do:

```python

>>> help(bs4_scraper.<method_name>)

```

### Other utility classes included in the module

- `Translator`
- `FileHandler`
- `Logger`
- `RequestLimitSetting`

For information on how to use these classes, do:

```python
from bs4_web_scraper.<module_name> import <class_name>

>>> help(<class_name>)

```


### Scraper Methods

#### `download_url`

The `download_url` method is used to download files from a web page or url. The following example shows how to download a file from a web page. A simple example usage is shown below:

```python

# Downloading a file from a web page
bs4_scraper.download_url(url="https://www.example.com/download/example.mkv", save_as="example.mkv", save_to="downloads")

```

#### `download_urls`

The `download_urls` method is used to download multiple files from multiple web pages or urls. The following example shows how to download multiple files from a web page. A simple example usage is shown below:

```python

# Downloading multiple files
urls = [
    "https://www.example.com/download/example1.mkv",
    "https://www.example.com/download/example2.mkv",
    "https://www.example.com/download/example3.mkv",
    "https://www.example.com/download/example4.mkv",
    "https://www.example.com/download/example5.mkv",
]

bs4_scraper.download_urls(urls=urls, save_to="downloads")

```
The define what each file should be saved as, you can pass the `save_as` alongside the url as a dictionary - `urls` becomes a list of dictionaries, as parameter to the `download_urls` method. The following example shows how to download multiple files from a web page and save them with different names

```python

urls = [
    {
        "url": "https://www.example.com/download/example1.mkv",
        "save_as": "example1.mkv"
    },
    {
        "url": "https://www.example.com/download/example2.mkv",
        "save_as": "example2.mkv"
    },
    {
        "url": "https://www.example.com/download/example3.mkv",
        "save_as": "example3.mkv"
    },
]

bs4_scraper.download_urls(urls=urls, save_to="downloads")

```

#### `find_all`




### Credits

- [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Requests](https://requests.readthedocs.io/en/master/)
- [Translators](https://pypi.org/project/translators/)


#### Contributors and feedbacks are welcome. For feedbacks, please open an issue or contact me at tioluwa.dev@gmail.com or on twitter [@ti_oluwa_](https://twitter.com/ti_oluwa_)

#### To contribute, please fork the repo and submit a pull request

#### If you find this module useful, please consider giving it a star. Thanks!