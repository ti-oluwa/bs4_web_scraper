from scripts.scraper import BS4WebScraper
from scripts.help import bs4_credentials_template, available_translation_engines


# create a scraper object
bs4_scraper = BS4WebScraper(base_storage_dir='../', parser='html.parser',
                             log_filepath='..\logs\\bs4_scraper.log', scrape_session_pause_duration=5)

# Scrape just the first page (depth = 0) and translate to 'French'.
bs4_scraper.scrape(url='http://www.google.com/', scrape_depth=0, translate_to='fr')



# prints the credentials format for the scraper
print('Credentials format: ')
print(bs4_credentials_template, '\n')

# prints the available translation engines
print('Available translation engines: ')
print(available_translation_engines)

