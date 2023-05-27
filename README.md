## bs4_web_scraper

### __A web scraper based on the BeautifulSoup4 library with translation capabilities.__

[View Project on PyPI](https://pypi.org/project/bs4-web-scraper/)


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

# Scraping a web page and translating the scraped data to French
bs4_scraper = BS4WebScraper(...)
bs4_scraper.scrape(url="https://www.google.com", scrape_depth=0, translate_to="fr", translation_engine='google')

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
- `find_urls`
- `find_all_tags`
- `find_tags_by_id`
- `find_tags_by_class`
- `find_comments`
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

**Before proceeding, it is important to know what an 'rra' means. 'rra' stands for 'resource related attribute'. A resource related attribute is an attribute that is related to a file(resource) that the webpage is dependent on. For example, the `href` attribute of an `a` tag is a resource related attribute because it is related to the resource (link) that the `a` tag points to. The `src` attribute of an `img` tag is also a resource related attribute because it is related to the resource (image) that the `img` tag points to.**

#### `download_url`

The `download_url` method is used to download files from a web page or url. The following example shows how to download a file from a web page. A simple example usage is shown below:

```python

# Downloading a file from a web page
file_handler = bs4_scraper.download_url(url="https://www.example.com/download/example.mkv", save_as="example.mkv", save_to="downloads")

# Returns FileHandler Object for the downloaded file
print(file_handler.filename)
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

#### `find_urls`

This method is used to get all resource related attribute(url or link) on elements that match a given tag name. This method only works for tags that have the `src` or `href` attribute. The following example shows how to find all urls on the `img` elements in a web page:

```python
# Finding all urls on the img elements on a web page with a class of 'sub-image', saving them to a file and downloading them

img_urls = bs4_scraper.find_urls(url='https://example.com/',target="img", attrs={"class": "sub-image"})
# save the urls to a file using the save_results method
bs4_scraper.save_results(results=img_urls, file_path="downloads/img_urls.txt")
# download the urls using the download_urls method
bs4_scraper.download_urls(urls=img_urls, save_to="downloads")

```

#### `find_all_tags`

This method is used to get all elements that match a given tag name. A simple example usage is shown below:

```python

# Finding all small elements from a url going two levels deep
small_elements = bs4_scraper.find_all_tags(url='https://example.com/',target="small", depth=2)
print(small_elements)

```

#### `find_links`

This method is used to get the `href` on all `a` element. A simple example usage is shown below:

```python

# Finding all links on a web page
links = bs4_scraper.find_links(url='https://example.com/')
print(links)

```

**All `find_*` methods have the same usage as the `find_links` method. For example, the `find_stylesheets` method is used to get the `href` on all `link` element with a `rel` attribute of `stylesheet`. A simple example usage is shown below:**

```python

# Finding all stylesheets on a web page
stylesheets = bs4_scraper.find_stylesheets(url='https://example.com/')
print(stylesheets)

```

#### `find_pattern`

This method is used to find all elements that match a given REGEX pattern. A simple example usage is shown below:

```python

# Finding all elements that match a email REGEX pattern
pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
emails = bs4_scraper.find_pattern(url='https://example.com/', regex=pattern)
print(emails)

```

### Utility Classes

#### `Translator`

This class is simply used to translate text, a file or soup from one language to another. The following example shows how to translate text from English to Yoruba:

```python
from bs4_web_scraper.translate import Translator

# Translating text from English to Yoruba
translator = Translator(translation_engine="google")
translated_text = translator.translate(content="Hello World", src_lang="en", target_lang="yo")
print(translated_text)

# If content is markup
translated_text = translator.translate(content="<p>Hello World</p>", src_lang="en", target_lang="yo", is_markup=True)
print(translated_text)

```

To translate a file, you can pass the file path to the `translate` method as shown below:

```python

# Translating a file from English to Yoruba
translator = Translator(translation_engine="google")
translated_file_handler = translator.translate_file(file_path="path/to/file.txt", src_lang="en", target_lang="yo")
print(translated_file_handler.file_content)

```

To translate a soup object, you can pass the soup object to the `translate` method as shown below:

```python

# Translating a soup object from English to Yoruba
translator = Translator(translation_engine="google")
translated_soup = translator.translate(content=soup, src_lang="en", target_lang="yo")

```
For specificity, you can use the `translate_text`, `translate_markup` or `translate_soup` methods to translate text, markup or a soup respectively. 


#### `FileHandler`

The `FileHandler` class is used to handle files and perform basic read-write operations on supported file types.

**Example Usage**

```python
from bs4_web_scraper.file_handler import FileHandler

# Instantiating a FileHandler object
file_handler = FileHandler(file_path="path/to/file.txt")

# Opening the file
file_handler.open_file()

# Closing the file
file_handler.close_file()

# Reading the file
file_content = file_handler.read_file(read_mode='r')
print(file_content)

# Writing to the file
file_handler.write_to_file(content="Hello World", write_mode='w')

# Appending to the file
file_handler.write_to_file(content="Hello World", write_mode='a')

# Copying the file
file_handler.copy_to(destination="path/to/copy.txt")

# Moving the file
file_handler.move_to(destination="path/to/move.txt")

# Clearing the file content
file_handler.clear_file()

# Deleting the file
file_handler.delete_file()

# Getting the file type
file_type = file_handler.filetype
print(file_type)

# Getting the file name
file_name = file_handler.name
print(file_name)

# Getting the file path
file_path = file_handler.filepath
print(file_path)

```


#### `Logger`

This class is used to log messages to a file and/or console. The following example shows how to log messages to a file:

```python
from bs4_web_scraper.logging import Logger

# Instantiating a Logger object
logger = Logger(name="example_logger", log_filepath="path/to/log.txt")

# To log the message to the console also
logger.to_console = True

# Set the log level
logger.set_base_level(level="DEBUG")

# Log a message
logger.log(message="Hello World") # Default log level is INFO

# Log a message with a specific log level
logger.log(message="Hello World", level="DEBUG")

```
The base log level can be set to any of the following: `DEBUG`, `INFO`, `WARNING`, `ERROR` or `CRITICAL`. The default log level is `NOTSET`. The `to_console` attribute is set to `False` by default. To log messages to the console, set the `to_console` attribute to `True` as shown in the example above. You cannot log at levels below the base log level. For example, if the base log level is set to `INFO`, you cannot log at `DEBUG` level.




### Credits

- [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Requests](https://requests.readthedocs.io/en/master/)
- [Translators](https://pypi.org/project/translators/)


#### Contributors and feedbacks are welcome. For feedbacks, please open an issue or contact me at tioluwa.dev@gmail.com or on twitter [@ti_oluwa_](https://twitter.com/ti_oluwa_)

#### To contribute, please fork the repo and submit a pull request

#### If you find this module useful, please consider giving it a star. Thanks!