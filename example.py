from scripts.scraper import BS4WebScraper
from scripts.help import bs4_credentials_template, available_translation_engines

# create a scraper object
bs4_scraper = BS4WebScraper(base_storage_dir='../', parser='html.parser',
                             log_filename='..\logs\\bs4_scraper.log')
bs4_scraper.scrape('https://www.google.com/', 0, translate_to='fr')


# prints the credentials format for the scraper
print('Credentials format: ')
print(bs4_credentials_template, '\n')

# prints the available translation engines
print('Available translation engines: ')
print(available_translation_engines)

