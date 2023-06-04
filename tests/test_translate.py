import unittest
from bs4 import BeautifulSoup, Tag


from bs4_web_scraper.file_handler import FileHandler
from bs4_web_scraper.translate import Translator


class TestTranslator(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.translator = Translator()
        cls.markup = "<html><body><h1>Hello World</h1><p>Testing</p></body></html>"
        
    @classmethod
    def tearDownClass(cls) -> None:
        pass

    def test_supported_languages(self):
        supported_langs = self.translator.supported_languages
        self.assertIsInstance(supported_langs, dict)
        self.assertIsNot(supported_langs, {})

    def test_lang_is_supported(self):
        self.assertTrue(self.translator.lang_is_supported('en'))
        self.assertFalse(self.translator.lang_is_supported('xx'))

    def test_set_target_and_src_lang(self):
        self.translator.set_target_and_src_lang('en', 'es')
        self.assertTrue(self.translator.target_language == 'en')
        self.assertTrue(self.translator.source_language == 'es')

    def test_add_translatable_element(self):
        self.translator.add_translatable_element('p')
        self.assertIn('p', self.translator._translatable_elements)

    def test_remove_translatable_element(self):
        self.translator.remove_translatable_element('p')
        self.assertNotIn('p', self.translator._translatable_elements)
        self.translator.add_translatable_element('p')

    def test_detect_language(self):
        detected_lang = self.translator.detect_language('Hello world!')
        self.assertTrue(bool(detected_lang))
        self.assertIsInstance(detected_lang, dict)
        self.assertEqual(detected_lang.get('language', None), 'en')

    def test_translate_text(self):
        translated_text = self.translator.translate_text('Hello world!', target_lang='fr')
        self.assertTrue(bool(translated_text))
        self.assertIsInstance(translated_text, str)
        translated_text_lang = self.translator.detect_language(translated_text).get('language', None)
        self.assertEqual(translated_text_lang, 'fr')

    def test_translate_markup(self):
        translated_markup = self.translator.translate_markup(self.markup, target_lang='fr')
        soup = BeautifulSoup(translated_markup, 'lxml')
        self.assertIsNotNone(soup.find('h1'))
        self.assertIsNotNone(soup.find('p'))
        translated_markup_lang = self.translator.detect_language(soup.get_text()).get('language', None)
        self.assertEqual(translated_markup_lang, 'fr')

    def test_translate_soup_tag(self):
        tag = BeautifulSoup(self.markup, 'lxml').find('h1')
        self.assertIsInstance(tag, Tag)
        try:
            self.translator.translate_soup_tag(tag, target_lang='fr')
            translated_tag_lang = self.translator.detect_language(tag.get_text()).get('language', None)
            self.assertEqual(translated_tag_lang, 'fr')
        except Exception as e:
            self.fail(e.__str__())

    def test_translate_soup(self):
        soup = BeautifulSoup(self.markup, 'lxml')
        translated_soup = self.translator.translate_soup(soup, target_lang='fr')
        self.assertIsInstance(translated_soup, BeautifulSoup)
        translated_soup_lang = self.translator.detect_language(translated_soup.get_text()).get('language', None)
        self.assertEqual(translated_soup_lang, 'fr')

    def test_translate_file(self):
        translated_file_handler = self.translator.translate_file('./tests/fixtures/test.txt', target_lang='fr')
        self.assertIsInstance(translated_file_handler, FileHandler)
        translated_file_handler_lang = self.translator.detect_language(translated_file_handler.file_content).get('language', None)
        self.assertEqual(translated_file_handler_lang, 'fr')


if "__name__" == "__main__":
    unittest.main()





