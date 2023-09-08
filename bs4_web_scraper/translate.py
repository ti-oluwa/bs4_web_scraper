"""
DESCRIPTION: ::
    This module contains the Translator class for translating text and markup (html, xml, xhtml...) content using the `translators` package.

    Avoid making high frequency requests to the translation engine. This may result in your IP address being blocked.
    Enterprises provide free services, we should be grateful instead of making trouble.
"""

from typing import Dict, List
import time
import copy
import random
from bs4 import BeautifulSoup
from bs4.element import Tag
from concurrent.futures import ThreadPoolExecutor
try:
    import translators as ts
    from translators.server import TranslatorsServer, tss
except Exception as exc:
    raise ConnectionError(f"Could not import `translators` module: {exc}")

from . import utils
from .logger import Logger
from .file_handler import FileHandler
from .exceptions import TranslationError, UnsupportedLanguageError



translation_engines = ts.translators_pool


class Translator:
    """
    #### Translator class for translating text and markup content using the `translators` package.

    #### Parameters:
    @param `translation_engine` (str): The translation engine to be used. Defaults to "bing".

    #### Attributes: ::
    @attr `translation_engine` (str): The translation engine to be used. Defaults to "bing".
    @attr `target_language` (str): The target language to translate to. Defaults to None.
    @attr `source_language` (str): The source language to translate from. Defaults to None.
    @attr `_cache` (Dict[str, str]): A cache for storing translations to manage translation cost. Defaults to an empty dict.
    @attr `_translatable_elements` (List[str]): A list of markup elements whose text can be translated. 
    A defaults to a list of markup elements have been provided. To add more elements,
    use the `add_translatable_element` method. To remove elements, use the `remove_translatable_element` method.
    @attr supported_languages (dict): A dictionary of all languages supported by the chosen translation engine.

    #### Currently supported translation engines:
    * 'alibaba'
    * 'argos'
    * 'baidu'
    * 'bing'
    * 'caiyun'
    * 'deepl'
    * 'google'
    * 'iciba'
    * 'iflytek'
    * 'itranslate'
    * 'lingvanex'
    * 'niutrans'
    * 'mglip'
    * 'papago'
    * 'reverso'
    * 'sogou'
    * 'tencent'
    * 'translateCom'
    * 'utibet'
    * 'yandex'
    * 'youdao'
    
    """
    logger: Logger = None
    translation_engine: str = 'bing'
    _server: TranslatorsServer = tss
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

    def __init__(self, translation_engine: str = "bing", ) -> None:
        self.translation_engine = translation_engine

    @property
    def server(self):
        return self._server

    @property
    def supported_languages(self) -> dict:
        if self.translation_engine:
            args = ('yes','en', 'am')
            func = lambda f: getattr(self._server, f"{self.translation_engine}")(*f)
            func(args)
            return getattr(self._server, f"_{self.translation_engine}").language_map
        return {}


    def detect_language(self, _s: str) -> Dict:
        """
        Detects the language of the specified text.

        NOTE: This method is not guaranteed to work always.
        An example of a case where the function does not work is in detecting Amharic.

        Returns a dictionary containing the language code and confidence score.

        Args:
            _s (str): The text to detect the language of.
        """
        try:
            details = self.server.translate_text(query_text=_s, translator='bing', is_detail_result=True)
        except:
            return {}
        return details.get('detectedLanguage', {}) if details else {}

    
    def _log(self, message: str, level: str | None = None) -> None:
        '''
        Logs a message using `self.logger` or prints it out if `self.logger` is None.

        Args:
            message (str): The message to log
            level (str | None): The level of message to log.
        '''
        if self.logger and isinstance(self.logger, Logger):
            self.logger.log(message, level)
        elif self.logger and not isinstance(self.logger, Logger):
            raise TypeError('Invalid type for `self.logger`. `self.logger` should be an instance of bs4_web_scraper.logging.Logger')
        return print(message + '\n') 
    

    def lang_is_supported(self, lang_code: str) -> bool:
        '''
        Check if the specified language code is supported by `self.translation_engine`
        
        Returns True if supported, else False.

        Args:
            lang_code (str): The language code to check.
        
        '''
        lang_code = lang_code.strip().lower()
        if not lang_code:
            raise TranslationError("`lang_code` cannot be empty")
        return bool(self.supported_languages.get(lang_code, None)) if self.supported_languages else False


    def set_target_and_src_lang(self, target_lang: str, src_lang: str = 'auto') -> None:
        """
        Sets both `self.target_language` and `self.source_language`
        """
        self.set_translator_target(target_lang)
        self.set_translator_source(src_lang)
        return None


    def set_translator_target(self, target_lang: str) -> None:
        '''
        Sets the instance's target language for translation.

        Args:
            target_lang (str): The target language for translation.
        
        '''
        if target_lang and not self.lang_is_supported(target_lang):
            raise UnsupportedLanguageError(
                "Unsupported target language for translation", 
                target_lang, 
                self.translation_engine
            )
        self.target_language = target_lang.strip().lower()


    def set_translator_source(self, src_lang: str) -> None:
        '''
        Sets the instance's source language for translation.

        Args:
            src_lang (str): The source language for translation.
        
        '''
        if src_lang and src_lang != 'auto' and not self.lang_is_supported(src_lang):
            raise UnsupportedLanguageError(
                "Unsupported source language for translation", 
                src_lang, 
                self.translation_engine
            )
        self.source_language = src_lang.strip().lower()


    def add_translatable_element(self, element: str) -> None:
        '''
        Adds an markup element to the list of translatable elements.

        Args:
            element (str): The markup element to be added to the list of translatable elements.
        '''
        if not isinstance(element, str):
            raise TypeError("Invalid type for `element`")
        # Check if element is a valid markup element
        markup_element = BeautifulSoup(f"<{element}></{element}>", 'lxml').find(element)
        if markup_element:
            self._translatable_elements.append(element)
            self._translatable_elements = list(set(self._translatable_elements))
        else:
            raise ValueError(f"Invalid markup element: {element}")


    def remove_translatable_element(self, element: str) -> None:
        '''
        Removes an markup element from the list of translatable elements.

        Args:
            element (str): The markup element to be removed from the list of translatable elements.
        '''
        if element in self._translatable_elements:
            return self._translatable_elements.remove(element)
        return None


    def translate(
            self, 
            content: str | bytes | BeautifulSoup, 
            src_lang: str="auto", 
            target_lang: str="en", 
            cache: bool=True, 
            is_markup: bool=False, 
            **kwargs
        ) -> str | bytes:
        '''
        Translate `content` from `src_lang` to `target_lang`.

        Returns translated content.

        Args:
            content (str | bytes | BeatifulSoup): Content to be translated
            src_lang (str, optional): Source language. Defaults to "auto".
            target_lang (str, optional): Target language. Defaults to "en".
            cache (bool, optional): Whether to cache translations. Defaults to True.
            is_markup (bool, optional): Whether `content` is markup. Defaults to False.
            **kwargs: Keyword arguments to be passed to `self.translate_text` or `self.translate_markup`.
        '''
        if is_markup:
            return self.translate_markup(content, src_lang, target_lang, **kwargs)
        elif isinstance(content, BeautifulSoup):
            return self.translate_soup(content, src_lang, target_lang, **kwargs)
        return self.translate_text(content, src_lang, target_lang, cache, **kwargs)
        
    
    def translate_text(
            self, 
            text: str, 
            src_lang: str="auto", 
            target_lang: str="en", 
            cache: bool=True, 
            **kwargs
        ) -> str:
        '''
        Translate text from `src_lang` to `target_lang`.

        Returns translated text.

        Args::
            text (str): Text to be translated
            src_lang (str, optional): Source language. Defaults to "auto".
            target_lang (str, optional): Target language. Defaults to "en".
            cache (bool, optional): Whether to cache translations. Defaults to True.
            **kwargs: Keyword arguments to be passed to `translators.translate_text`.
                    :param is_detail_result: boolean, default False.
                    :param professional_field: str, support baidu(), caiyun(), alibaba() only.
                    :param timeout: float, default None.
                    :param proxies: dict, default None.
                    :param sleep_seconds: float, default random.random().
                    :param update_session_after_seconds: float, default 1500.
                    :param if_use_cn_host: bool, default False.
                    :param reset_host_url: str, default None.
                    :param if_ignore_empty_query: boolean, default False.
                    :param if_ignore_limit_of_length: boolean, default False.
                    :param limit_of_length: int, default 5000.
                    :param if_show_time_stat: boolean, default False.
                    :param show_time_stat_precision: int, default 4.
                    :param lingvanex_model: str, default 'B2C'.
        '''
        self.set_target_and_src_lang(target_lang, src_lang)
        kwargs_ = {
            'if_ignore_empty_query': True,
        }
        kwargs_.update(kwargs)
        try:
            if cache:
                if self._cache.get(text, None):
                    return self._cache[text]
                else:
                    translated_text = self.server.translate_text(
                        query_text=text, 
                        to_language=target_lang, 
                        from_language=src_lang, 
                        translator=self.translation_engine, 
                        **kwargs_
                    )
                    self._cache[text] = translated_text
                    return translated_text
            return self.server.translate_text(
                query_text=text, 
                to_language=target_lang, 
                from_language=src_lang, 
                translator=self.translation_engine, 
                **kwargs_
            )
        except Exception as e:
            error_ = TranslationError(f"Error translating text: {e}")
            self._log(f"{error_}", level='error')
            return text


    def translate_markup(
            self, 
            markup: str | bytes, 
            src_lang: str="auto", 
            target_lang: str="en", 
            **kwargs
        ) -> str | bytes:
        '''
        Translates markup.

        Returns the translated markup.

        Args:
            markup (str | bytes): markup content to be translated
            src_lang (str, optional): Source language. Defaults to "auto".
            target_lang (str, optional): Target language. Defaults to "en".
            **kwargs: Keyword arguments to be passed to `translators.translate_markup`.
                    :param professional_field: str, support baidu(), caiyun(), alibaba() only.
                    :param timeout: float, default None.
                    :param proxies: dict, default None.
                    :param sleep_seconds: float, default random.random().
                    :param update_session_after_seconds: float, default 1500.
                    :param if_use_cn_host: bool, default False.
                    :param reset_host_url: str, default None.
                    :param if_ignore_empty_query: boolean, default False.
                    :param if_ignore_limit_of_length: boolean, default False.
                    :param limit_of_length: int, default 5000.
                    :param if_show_time_stat: boolean, default False.
                    :param show_time_stat_precision: int, default 4.
                    :param lingvanex_model: str, default 'B2C'.
        '''
        if not isinstance(markup, (str, bytes)):
            raise TypeError("Invalid type for `markup`")
        is_bytes = isinstance(markup, bytes)
        kwargs.pop('is_detail_result', None)
        soup = BeautifulSoup(markup, 'lxml')
        translated_markup = self.translate_soup(soup, src_lang, target_lang, **kwargs).prettify()

        # re-encode the markup if the initial markup was in bytes
        if is_bytes:
            translated_markup = translated_markup.encode('utf-8')
        return translated_markup


    # NOT FUNCTIONAL FOR NOW
    # def translate_markup(self, markup: str | bytes, src_lang: str="auto", target_lang: str="en", **kwargs):
    #     '''
    #     Translates the markup content from `src_lang` to `target_lang`.

    #     ### NOT FUNCTIONAL FOR NOW. CONVERT markup TO BEAUTIFULSOUP OBJECT AND USE THE `translate_soup` METHOD INSTEAD.

    #     Returns translated markup.

    #     Args:
    #         markup (str | bytes): markup content to be translated
    #         src_lang (str, optional): Source language. Defaults to "auto".
    #         target_lang (str, optional): Target language. Defaults to "en".
    #         **kwargs: Keyword arguments to be passed to `translators.translate_markup`.
    #                 :param is_detail_result: boolean, default False.
    #                 :param professional_field: str, support baidu(), caiyun(), alibaba() only.
    #                 :param timeout: float, default None.
    #                 :param proxies: dict, default None.
    #                 :param sleep_seconds: float, default random.random().
    #                 :param update_session_after_seconds: float, default 1500.
    #                 :param if_use_cn_host: bool, default False.
    #                 :param reset_host_url: str, default None.
    #                 :param if_ignore_empty_query: boolean, default False.
    #                 :param if_ignore_limit_of_length: boolean, default False.
    #                 :param limit_of_length: int, default 5000.
    #                 :param if_show_time_stat: boolean, default False.
    #                 :param show_time_stat_precision: int, default 4.
    #                 :param lingvanex_model: str, default 'B2C'.
    #     '''
    #     if not isinstance(markup, (str, bytes)):
    #         raise TypeError("Invalid type for `markup`")
    #     self.set_target_and_src_lang(target_lang, src_lang)
    #     kwargs_ = {
    #         'if_ignore_empty_query': True,
    #     }
    #     kwargs_.update(kwargs)
    #     markup = markup.decode('utf-8') if isinstance(markup, bytes) else markup
    #     try:
    #         translated_markup = ts.translate_markup(
    #                                         markup_text=markup, to_language=target_lang, from_language=src_lang, 
    #                                         translator=self.translation_engine, **kwargs_
    #                                         )
    #         return translated_markup
    #     except Exception as e:
    #         error_ = TranslationError(f"Error translating markup: {e}") 
    #         self._log(f"{error_}", level='error')
    #         return markup


    def translate_file(
            self, 
            filepath: str, 
            src_lang: str="auto", 
            target_lang: str="en", 
            **kwargs
        ):
        '''
        Translates file from `src_lang` to `target_lang`.

        Returns translated file's FileHandler`.

        Supported file types include: .txt, .csv, .doc, .docx, .pdf, .md..., mostly files with text content.

        Args::
            * filepath (str): path to the file to be translated.
            * src_lang (str, optional): Source language. Defaults to "auto".
            * target_lang (str, optional): Target language. Defaults to "en".
            * **kwargs: Keyword arguments to be passed to `translators.translate_text`.
                    :param professional_field: str, support baidu(), caiyun(), alibaba() only.
                    :param timeout: float, default None.
                    :param proxies: dict, default None.
                    :param sleep_seconds: float, default random.random().
                    :param update_session_after_seconds: float, default 1500.
                    :param if_use_cn_host: bool, default False.
                    :param reset_host_url: str, default None.
                    :param if_ignore_empty_query: boolean, default False.
                    :param if_ignore_limit_of_length: boolean, default False.
                    :param limit_of_length: int, default 5000.
                    :param if_show_time_stat: boolean, default False.
                    :param show_time_stat_precision: int, default 4.
                    :param lingvanex_model: str, default 'B2C'.
        '''
        self.set_target_and_src_lang(target_lang, src_lang)
        kwargs_ = {
            'if_ignore_empty_query': True,
        }
        kwargs.pop('is_detail_result', None)
        kwargs_.update(kwargs)
        file_handler = FileHandler(filepath, not_found_ok=False)
        file_content = file_handler.file_content

        if file_handler.filetype in ['xhtml', 'htm', 'shtml', 'html', 'xml']:
            translated_markup = self.translate_markup(file_content, src_lang, target_lang, **kwargs)
            file_handler.write_to_file(translated_markup, 'w')
            file_handler.close_file()
            return file_handler

        slice_size = kwargs_.get('limit_of_length', 4000)
        contents = utils.slice_iterable(file_content, slice_size)
        try:
            translated_contents = list(map(lambda text: self.translate_text(text, src_lang, target_lang, False, **kwargs_), contents))
            translated_text = "".join(translated_contents)
            file_handler.write_to_file(translated_text, write_mode='w+')
            file_handler.close_file()
            return file_handler
        except Exception as e:
            raise TranslationError(f"File cannot be translated. {e}")


    def translate_soup_tag(
            self, 
            element: Tag, 
            src_lang: str = "auto", 
            target_lang: str = "en", 
            _ct: int = 0, 
            **kwargs
        ) -> None:
        '''
        Translates the text of a BeautifulSoup element.

        NOTE: 
        * This function is not meant to be called directly. Use `translate_soup` instead.
        * This function is recursive.
        * This function modifies the element in place.
        * Translations are cached by default to avoid repeated translations which can be costly.

        Args:
            `element` (bs4.element.Tag): The element whose text is to be translated.
            `src_lang` (str, optional): Source language. Defaults to "auto".
            `target_lang` (str, optional): Target language. Defaults to "en".
            `_ct` (int, optional): The number of times the function has been called recursively. Defaults to 0.
            Do not pass this argument manually.

        Raises:
            TypeError: If `element` is not a BeautifulSoup element.
            TypeError: If `_ct` is not an integer.
        '''
        if not isinstance(element, Tag):
            raise TypeError("Invalid type for `element`")
        if not isinstance(_ct, int):
            raise TypeError("Invalid type for `_ct`")

        if element.string and element.string.strip():
            initial_string = copy.copy(element.string)
            cached_translation = self._cache.get(element.string, None)
            if cached_translation:
                element.string.replace_with(cached_translation)
            else:
                try:
                    translation = self.translate_text(text=element.string, src_lang=src_lang, target_lang=target_lang, **kwargs)
                    element.string.replace_with(translation)
                except Exception as e:
                    error_ = TranslationError(f"Error translating element: {e}")
                    self._log(f'{error_}', level='error')
                    _ct += 1
                    time.sleep(random.random(2, 5) * _ct)
                    if _ct <= 3:
                        return self.translate_soup_tag(element, _ct)
                finally:
                    self._cache[initial_string] = translation
        return None


    def translate_soup(
            self, 
            soup: BeautifulSoup, 
            src_lang: str = "auto", 
            target_lang: str = "en", 
            thread: bool = True, 
            **kwargs
        ) -> BeautifulSoup:
        '''
        Translates the text of a BeautifulSoup object.

        NOTE:
        * This function is not thread-safe if `thread` is set to True.

        Args:
            soup (BeautifulSoup): The BeautifulSoup object whose text is to be translated.
            src_lang (str, optional): Source language. Defaults to "auto".
            target_lang (str, optional): The target language for translation. Defaults to "en".
            thread (bool, optional): Whether to use multi-threading to translate the text. Defaults to True.
            **kwargs: Keyword arguments to be passed to `translators.translate_soup_tag`.

        Returns:
            BeautifulSoup: The translated BeautifulSoup object.

        Raises:
            TypeError: If `soup` is not a BeautifulSoup object.
        '''
        if not isinstance(soup, BeautifulSoup):
            raise TypeError("Invalid type for `soup`")
        self.set_target_and_src_lang(target_lang, src_lang)
        elements_ = soup.find_all(self._translatable_elements)
        translatable_elements = list(filter(lambda el: bool(el.string), elements_))
        if thread:
            with ThreadPoolExecutor() as executor:
                for item_list in utils.slice_iterable(translatable_elements, 50):
                    _ = executor.map(lambda item: self.translate_soup_tag(item, src_lang, target_lang, **kwargs), item_list)
                    time.sleep(random.randint(3, 5))
        else:
            for element in translatable_elements:
                self.translate_soup_tag(element)
        return soup
