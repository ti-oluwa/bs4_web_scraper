'''
DESCRIPTION: ::
    This script helps user with a few tools to configure the bs4_web_scraper for use.
'''

import translators as ts


bs4_credentials_template = {
    'auth_url': '<Login URL>',
    'auth_username_field': '<Username Field>',
    'auth_password_field': '<Password Field>',
    'auth_username': '<Username>',
    'auth_password': '<Password>',
}
available_translation_engines = ts.translators_pool