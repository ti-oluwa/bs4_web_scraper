"""
DESCRIPTION: ::
    This module contains the Translator class for translating text and html content using the `translators` package.

    Avoid making high frequency requests to the translation engine. This may result in your IP address being blocked.
    Enterprises provide free services, we should be grateful instead of making trouble.
"""

from typing import Dict, List
import time
import copy
from bs4 import BeautifulSoup
from bs4.element import Tag
import translators as ts
from translators.server import TranslatorsServer, tss

from .utils import Logger



class Translator:
    """
    Translator class for translating text and html content using the `translators` package.

    Parameters:
        translation_engine (str): The translation engine to be used. Defaults to "google".

    Attributes: ::
        translation_engine (str): The translation engine to be used. Defaults to "google".
        target_language (str): The target language to translate to. Defaults to None.
        source_language (str): The source language to translate from. Defaults to None.
        _cache (Dict[str, str]): A cache for storing translations. Defaults to an empty dict.
        _translatable_elements (List[str]): A list of HTML elements whose text can be translated. 
        A defaults to a list of HTML elements have been provided. To add more elements,
        use the `add_translatable_element` method. To remove elements, use the `remove_translatable_element` method.
        supported_languages (dict): A dictionary of all languages supported by the chosen translation engine.

    #### Currently supported translation engines:
    - 'alibaba'
    - 'argos'
    - 'baidu'
    - 'bing'
    - 'caiyun'
    - 'deepl'
    - 'google'
    - 'iciba'
    - 'iflytek'
    - 'itranslate'
    - 'lingvanex'
    - 'niutrans'
    - 'mglip'
    - 'papago'
    - 'reverso'
    - 'sogou'
    - 'tencent'
    - 'translateCom'
    - 'utibet'
    - 'yandex'
    - 'youdao'
    
    """
    logger: Logger = None
    translation_engine: str = 'google'
    server: TranslatorsServer = tss
    target_language: str = None
    source_language: str = None
    _cache: Dict[str, str] = {}
    _translatable_elements: List[str] = [
        'h1', 'u', 's', 'abbr', 'del', 'pre', 'h5', 'sub', 'kbd', 'li', 
        'dd', 'textarea', 'dt', 'input', 'em', 'sup', 'label', 'button', 'h6', 
        'title', 'dfn', 'th', 'acronym', 'cite', 'samp', 'td', 'p', 'ins', 'big', 
        'caption', 'bdo', 'var', 'h3', 'tt', 'address', 'h4', 'legend', 'i', 
        'small', 'b', 'q', 'option', 'code', 'h2', 'a', 'strong', 'span',
    ]

    def __init__(self, translation_engine: str = "google", ) -> None:
        if not isinstance(translation_engine, str):
            raise ValueError('Invalid type for translation engine')

        self.translation_engine = translation_engine


    @property
    def supported_languages(self) -> dict:
        if self.translation_engine:
            args = ('yes','en', 'zh')
            func = lambda f: getattr(self.server, f"{self.translation_engine}")(*f)
            func(args)
            return getattr(self.server, f"_{self.translation_engine}").language_map
        return {}

    
    def _log(self, message: str, type: str = 'info') -> None:
        '''
        Logs a message using `self.logger` or prints it out if `self.logger` is None.

        Args:
            message (str): The message to log
            type (str): The type of message to log. Defaults to 'info'.
        '''
        if self.logger and not isinstance(self.logger, Logger):
            raise ValueError('Invalid type for `self.logger`')
        if not isinstance(message, str):
            raise ValueError('Invalid type for `message`')
        if not isinstance(type, str):
            raise ValueError('Invalid type for `type`')
        if type.lower() not in ['info', 'warning', 'error', 'debug']:
            raise ValueError('Invalid value for `type`')
        if self.logger:
            self.logger.log(message, level=type.upper())
        else:
            print(message)    


    def add_translatable_element(self, element: str) -> None:
        '''
        Adds an HTML element to the list of translatable elements.

        Args:
            element (str): The HTML element to be added to the list of translatable elements.
        '''
        if not isinstance(element, str):
            raise ValueError("Invalid type for `element`")
        # check if element is a valid HTML element
        html_element = BeautifulSoup(f"<{element}></{element}>", 'html.parser').find(element)
        if html_element:
            self._translatable_elements.append(element)
            self._translatable_elements = list(set(self._translatable_elements))
        else:
            raise ValueError(f"Invalid HTML element: {element}")


    def remove_translatable_element(self, element: str) -> None:
        '''
        Removes an HTML element from the list of translatable elements.

        Args:
            element (str): The HTML element to be removed from the list of translatable elements.
        '''
        if not isinstance(element, str):
            raise ValueError("Invalid type for `element`")
        if element in self._translatable_elements:
            self._translatable_elements.remove(element)

    
    def translate_text(self, text: str, src_lang: str="auto", target_lang: str="en") -> str:
        '''
        Translate text from `src_lang` to `target_lang` using `self.translator`.

        Returns translated text.

        Args:
            text (str): Text to be translated
            src_lang (str, optional): Source language. Defaults to "auto".
            target_lang (str, optional): Target language. Defaults to "en".

        '''
        if not isinstance(text, str):
            raise ValueError("Invalid type for `text`")
        if not isinstance(src_lang, str):
            raise ValueError("Invalid type for `src_lang`")
        if not isinstance(target_lang, str):
            raise ValueError("Invalid type for `target_lang`")

        translated_text = ts.translate_text(query_text=text, to_language=target_lang, 
                                            from_language=src_lang, translator=self.translation_engine)
        return translated_text

    # NOT FUNCTIONAL FOR NOW
    # def translate_html(self, html: str | bytes, src_lang: str="auto", target_lang: str="en"):
    #     '''
    #     Translates the html content from `src_lang` to `target_lang` using `self.translator`.

    #     Returns translated html.
    #     Args:
    #         html (str | bytes): HTML content to be translated
    #         src_lang (str, optional): Source language. Defaults to "auto".
    #         target_lang (str, optional): Target language. Defaults to "en".
    #     '''
    #     if not isinstance(html, (str, bytes)):
    #         raise ValueError("Invalid type for `html`")
    #     if not isinstance(src_lang, str):
    #         raise ValueError("Invalid type for `src_lang`")
    #     if not isinstance(target_lang, str):
    #         raise ValueError("Invalid type for `target_lang`")

    #     html = html.decode('utf-8') if isinstance(html, bytes) else html
    #     translated_html = ts.translate_html(html_text=html, to_language=target_lang, from_language=src_lang, translator=self.translation_engine)
    #     print("TRANSLATION: ", translated_html)
    #     return translated_html


    def translate_soup_element(self, element: Tag, _ct: int = 0) -> None:
        '''
        Translates the text of a BeautifulSoup element.

        Args:
            element (bs4.element.Tag): The element whose text is to be translated.
            _ct (int, optional): The number of times the function has been called recursively. Defaults to 0.
            Do not pass this argument manually.
        
        '''
        if not isinstance(element, Tag):
            raise ValueError("Invalid type for `element`")
        if not isinstance(_ct, int):
            raise ValueError("Invalid type for `_ct`")

        if element.string.strip():
            initial_string = copy.copy(element.string)
            cached_translation = self._cache.get(element.string, None)
            if cached_translation:
                element.string.replace_with(cached_translation)
            else:
                try:
                    translation = self.translate_text(text=element.string, target_lang=self.target_language)
                    element.string.replace_with(translation)
                except Exception as e:
                    self._log(f'{e}\n', type='error')
                    _ct += 1
                    time.sleep(10 * _ct)
                    if _ct <= 3:
                        return self.translator.translate_soup_element(element, _ct)
                else:
                    self._cache[initial_string] = translation


    def lang_is_supported(self, lang_code: str) -> bool:
        '''
        Check if the specified language code is supported by `self.translator`
        
        Returns True if supported, else False.

        Args:
            lang_code (str): The language code to check.
        
        '''
        if not isinstance(lang_code, str):
            raise ValueError("Invalid type for `lang_code`")
        lang_code = lang_code.strip().lower()
        if not lang_code:
            raise ValueError("`lang_code` cannot be empty")
        return bool(self.supported_languages.get(lang_code, None)) if self.supported_languages else False


    def set_translator_target(self, target_lang: str) -> None:
        '''
        Sets the instance's target language for translation.

        Args:
            target_lang (str): The target language for translation.
        
        '''
        if target_lang and not isinstance(target_lang, str):
            raise ValueError('`target_lang` should be of type str')
        if target_lang and not self.lang_is_supported(target_lang):
            raise Exception("Unsupported target language for translation")

        self.target_language = target_lang.strip().lower()


    def set_translator_source(self, src_lang: str) -> None:
        '''
        Sets the instance's source language for translation.

        Args:
            src_lang (str): The source language for translation.
        
        '''
        if src_lang and not isinstance(src_lang, str):
            raise ValueError('`src_lang` should be of type str')
        if src_lang and not self.lang_is_supported(src_lang):
            raise Exception("Unsupported source language for translation")

        self.source_language = src_lang.strip().lower()
        


