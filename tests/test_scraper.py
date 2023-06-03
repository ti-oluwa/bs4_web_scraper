import unittest
import os
import re
import csv
from bs4 import Comment, ResultSet, Tag

from tests import test_base
from bs4_web_scraper.scraper import BS4WebScraper
from bs4_web_scraper.file_handler import FileHandler



class TestBS4WebScraper(test_base.BaseTestClassForBS4Scraper):
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.scraper = BS4WebScraper(base_storage_dir='./tests/results')

    def test_scrape(self):
        try:
            self.scraper.scrape(self.scraper.base_url, scrape_depth=1)
        except Exception as e:
            self.fail(e.__str__())

    def test_download_urls(self):
        results = self.scraper.download_urls(test_base.urls)
        self.assertTrue(results != [])
        results = filter(lambda result: result is not None, results)
        map(lambda result: self.assertIsInstance(result, FileHandler), results)
        map(lambda result:self.assertTrue(os.path.exist(result.filepath)), results)

    def test_find_urls(self):
        # Reset base url. It was changed in the last method
        self.scraper.set_base_url(self.url)
        urls = self.scraper.find_urls(self.scraper.base_url, target='a', depth=1)
        self.assertIsInstance(urls, list)
        map(lambda url: self.assertIsInstance(url, str), urls)
        count = 20
        urls = self.scraper.find_urls(self.scraper.base_url, target='a', depth=1, count=count)
        self.assertTrue(len(urls) <= count)

    def test_find_all_tags(self):
        self.scraper.set_base_url(self.url)
        a_tags = self.scraper.find_all_tags(self.scraper.base_url, target='a', depth=1)
        self.assertIsInstance(a_tags, ResultSet)
        map(lambda a_tag: self.assertIsInstance(a_tag, Tag) and self.assertEqual(a_tag.name, 'a'), a_tags)
        count = 20
        a_tags = self.scraper.find_all_tags(self.scraper.base_url, target='a', depth=1, count=count)
        self.assertTrue(len(a_tags) <= count)

    def test_find_comments(self):
        self.scraper.set_base_url(self.url)
        comments = self.scraper.find_comments(self.scraper.base_url, depth=1)
        self.assertIsInstance(comments, ResultSet)
        map(lambda comment: self.assertIsInstance(comment, Comment), comments)
        count = 20
        comments = self.scraper.find_comments(self.scraper.base_url, depth=1, count=count)
        self.assertTrue(len(comments) <= count)

    def test_find_pattern(self):
        self.scraper.set_base_url(self.url)
        pattern = r'Eden Place'
        matches = self.scraper.find_pattern(self.scraper.base_url, regex=pattern, depth=1)
        self.assertIsInstance(matches, list)
        map(lambda match: self.assertIsInstance(match, str), matches)
        for match in matches:
           self.assertTrue(bool(re.match(pattern, match)))
        count = 20
        matches = self.scraper.find_pattern(self.scraper.base_url, regex=pattern, depth=1, count=count)
        self.assertTrue(len(matches) <= count)

    def test_save_results(self):
        urls = self.scraper.find_urls(self.url, target='img', count=10)
        if urls:
            self.scraper.save_results(urls, 'test_files/results.csv', csv_head="IMAGES")
            storage_path = f'{self.scraper.base_storage_dir}/test_files/results.csv'
            self.assertTrue(os.path.exists(storage_path))
            with open(storage_path, mode='rb') as csv_file:
                csv_reader = csv.reader(csv_file)
                for row in csv_reader:
                    self.assertEqual(row[1], 'IMAGES')
                    break

    def test_find_links(self):
        count = 10
        links = self.scraper.find_links(self.scraper.base_url, save_to_file=True, file_path='test_files/links.csv', count=count)
        self.assertIsInstance(links, list)
        map(lambda link: self.assertIsInstance(link, str), links)
        if links:
            self.assertTrue(os.path.exists(f'{self.scraper.base_storage_dir}/test_files/links.csv'))
        self.assertTrue(len(links) <= count)

    def test_find_stylesheets(self):
        count = 10
        stylesheets = self.scraper.find_stylesheets(self.scraper.base_url, save_to_file=True, file_path='test_files/stylesheets.csv', count=count)
        self.assertIsInstance(stylesheets, list)
        map(lambda stylesheet: self.assertIsInstance(stylesheet, str), stylesheets)
        if stylesheets:
            self.assertTrue(os.path.exists(f'{self.scraper.base_storage_dir}/test_files/stylesheets.csv'))
        self.assertTrue(len(stylesheets) <= count)

    def test_find_scripts(self):
        count = 10
        scripts = self.scraper.find_scripts(self.scraper.base_url, save_to_file=True, file_path='test_files/scripts.csv', count=count)
        self.assertIsInstance(scripts, list)
        map(lambda script: self.assertIsInstance(script, str), scripts)
        if scripts:
            self.assertTrue(os.path.exists(f'{self.scraper.base_storage_dir}/test_files/scripts.csv'))
        self.assertTrue(len(scripts) <= count)

    def test_find_fonts(self):
        count = 10
        fonts = self.scraper.find_fonts(self.scraper.base_url, save_to_file=True, file_path='test_files/fonts.csv', count=count)
        self.assertIsInstance(fonts, list)
        map(lambda font: self.assertIsInstance(font, str), fonts)
        self.assertTrue(os.path.exists(f'{self.scraper.base_storage_dir}/test_files/fonts.csv'))
        self.assertTrue(len(fonts) <= count)

    def test_find_images(self):
        count = 10
        images = self.scraper.find_images(self.scraper.base_url, save_to_file=True, file_path='test_files/images.csv', count=count)
        self.assertIsInstance(images, list)
        map(lambda image: self.assertIsInstance(image, str), images)
        if images:
            self.assertTrue(os.path.exists(f'{self.scraper.base_storage_dir}/test_files/images.csv'))
        self.assertTrue(len(images) <= count)

    def test_find_videos(self):
        count = 10
        videos = self.scraper.find_videos(self.scraper.base_url, save_to_file=True, file_path='test_files/videos.csv', count=count)
        self.assertIsInstance(videos, list)
        map(lambda video: self.assertIsInstance(video, str), videos)
        if videos:
            self.assertTrue(os.path.exists(f'{self.scraper.base_storage_dir}/test_files/videos.csv'))
        self.assertTrue(len(videos) <= count)

    def test_find_audios(self):
        count = 10
        audios = self.scraper.find_audios(self.scraper.base_url, save_to_file=True, file_path='test_files/audios.csv', count=count)
        self.assertIsInstance(audios, list)
        map(lambda audio: self.assertIsInstance(audio, str), audios)
        if audios:
            self.assertTrue(os.path.exists(f'{self.scraper.base_storage_dir}/test_files/audios.csv'))
        self.assertTrue(len(audios) <= count)

    def test_find_tags_by_id(self):
        count = 10
        id = 'base'
        tags = self.scraper.find_tags_by_id(self.scraper.base_url, id=id, count=count)
        self.assertIsInstance(tags, ResultSet)
        map(lambda tag: self.assertIsInstance(tag, Tag) and self.assertEqual(tag.get('id'), id), tags)
        self.assertTrue(len(tags) <= count)

    def test_find_tags_by_class(self):
        count = 10
        class_ = 'base'
        tags = self.scraper.find_tags_by_class(self.scraper.base_url, class_=class_, count=count)
        self.assertIsInstance(tags, ResultSet)
        map(lambda tag: self.assertIsInstance(tag, Tag) and self.assertEqual(tag.get('class'), class_), tags)
        self.assertTrue(len(tags) <= count)

    def test_find_emails(self):
        regex = r'[-|\w]+@\w+.\w{2,}'
        count = 10
        emails = self.scraper.find_emails(self.scraper.base_url, save_to_file=True, file_path='test_files/emails.csv', count=count)
        self.assertIsInstance(emails, list)
        map(lambda email: self.assertIsInstance(email, str), emails)
        for email in emails:
           self.assertTrue(bool(re.match(regex, email)))
        if emails:
            self.assertTrue(os.path.exists(f'{self.scraper.base_storage_dir}/test_files/emails.csv'))
        self.assertTrue(len(emails) <= count)

    def test_find_phone_numbers(self):
        regex = r'(\+\d{1,3})?[\s-]?(\d{7,16})'
        count = 10
        phone_numbers = self.scraper.find_phone_numbers(self.scraper.base_url, save_to_file=True, file_path='test_files/phone_numbers.csv', count=count)
        self.assertIsInstance(phone_numbers, list)
        map(lambda phone_number: self.assertIsInstance(phone_number, str), phone_numbers)
        for phone_number in phone_numbers:
           self.assertTrue(bool(re.match(regex, phone_number)))
        if phone_numbers:
            self.assertTrue(os.path.exists(f'{self.scraper.base_storage_dir}/test_files/phone_numbers.csv'))
        self.assertTrue(len(phone_numbers) <= count)


if "__name__" == "__main__":
    unittest.main()

