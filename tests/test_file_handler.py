import os
import unittest


from bs4_web_scraper.exceptions import FileError
from bs4_web_scraper.file_handler import FileHandler


class TestFileHandler(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.file_path = './tests/results/test_file_handler.txt'
        cls.file_handler = FileHandler(cls.file_path)
        cls.file_handler.file.write('testing')
        cls.file_handler.file.close()

    @classmethod
    def tearDownClass(cls):
        cls.file_handler.close_file()
    

    def test_init(self):
        self.assertTrue(os.path.isabs(self.file_handler.filepath))
        self.assertTrue(os.path.exists(self.file_handler.filepath))
        self.assertTrue(self.file_handler.filename == 'test_file_handler.txt')
        self.assertTrue(self.file_handler.filetype == 'txt')
        with self.assertRaises(TypeError):
            FileHandler(1).close_file()
        with self.assertRaises(FileError):
            FileHandler('./tests/results/').close_file()
        with self.assertRaises(FileNotFoundError):
            FileHandler('./tests/results/test_file_handler_2.txt', not_found_ok=False).close_file()
        with self.assertRaises(FileExistsError):
            FileHandler('./tests/results/test_file_handler.txt', exists_ok=False).close_file()

    def test_supported_file_types(self):
        self.assertIsInstance(self.file_handler.supported_file_types(), tuple)

    def test_open_file(self):
        try:
            # Read modes
            self.file_handler.open_file('r')
            self.assertTrue(self.file_handler.file.readable())
            self.file_handler.open_file('r+')
            self.assertTrue(self.file_handler.file.readable())
            self.assertTrue(self.file_handler.file.writable())
            self.file_handler.open_file('rb')
            self.assertTrue(self.file_handler.file.readable())
            self.file_handler.open_file('rb+')
            self.assertTrue(self.file_handler.file.readable())
            self.assertTrue(self.file_handler.file.writable())
            # Write modes
            self.file_handler.open_file('w')
            self.assertTrue(self.file_handler.file.writable())
            self.file_handler.open_file('w+')
            self.assertTrue(self.file_handler.file.writable())
            self.assertTrue(self.file_handler.file.readable())
            self.file_handler.open_file('wb')
            self.assertTrue(self.file_handler.file.writable())
            self.file_handler.open_file('wb+')
            self.assertTrue(self.file_handler.file.writable())
            self.assertTrue(self.file_handler.file.readable())
            # Append modes
            self.file_handler.open_file('a')
            self.assertTrue(self.file_handler.file.writable())
            self.file_handler.open_file('a+')
            self.assertTrue(self.file_handler.file.writable())
            self.assertTrue(self.file_handler.file.readable())
            self.file_handler.open_file('ab')
            self.assertTrue(self.file_handler.file.writable())
            self.file_handler.open_file('ab+')
            self.assertTrue(self.file_handler.file.writable())
            self.assertTrue(self.file_handler.file.readable())
        except Exception as e:
            self.fail(e.__str__())

    def test_close_file(self):
        try:
            self.file_handler.close_file()
            self.assertTrue(self.file_handler.file.closed)
        except Exception as e:
            self.fail(e.__str__())

    def test_read_file(self):
        # Read str
        self.assertIsInstance(self.file_handler.read_file('r'), str)
        # Read str plus
        self.assertIsInstance(self.file_handler.read_file('r+'), str)
        # Read bytes
        self.assertIsInstance(self.file_handler.read_file('rb'), bytes)
        # Read bytes plus    
        self.assertIsInstance(self.file_handler.read_file('rb+'), bytes)
        

    def test_write_to_file(self):
        try:
            # Write str
            self.file_handler.write_to_file("testing", 'w')
            # Write str plus
            self.file_handler.write_to_file("testing", 'w+')
            # Write bytes
            self.file_handler.write_to_file("testing".encode(self.file_handler.encoding), 'wb')
            # Write bytes plus    
            self.file_handler.write_to_file("testing".encode(self.file_handler.encoding), 'wb+')
            # Append str
            self.file_handler.write_to_file("testing", 'a')
            # Append str plus
            self.file_handler.write_to_file("testing", 'a+')
            # Append bytes
            self.file_handler.write_to_file("testing".encode(self.file_handler.encoding), 'ab')
            # Append bytes plus    
            self.file_handler.write_to_file("testing".encode(self.file_handler.encoding), 'ab+')
        except Exception as e:
            self.fail(e.__str__())

    def test_copy_to(self):
        try:
            self.file_handler.copy_to('./tests/test_files/')
            self.assertTrue(os.path.exists(f'./tests/test_files/{self.file_handler.filename}'))
        except Exception as e:
            self.fail(e.__str__())
    
    def test_move_to(self):
        try:
            prev_path = self.file_handler.filepath
            self.file_handler.move_to('./tests/test_files/')
            self.assertTrue(os.path.exists(f'./tests/test_files/{self.file_handler.filename}'))
            self.assertFalse(os.path.exists(prev_path))
        except Exception as e:
            self.fail(e.__str__())

    def test_json(self):
        self.file_handler.close_file()
        self.file_handler = FileHandler('./tests/results/test_file_handler.json')
        json_ = {
            "test": "123",
            "check": "ok",
        }
        self.file_handler.write_to_file(json_)
        file_content = self.file_handler.file_content
        self.assertEqual(file_content, json_)
        update_ = {
            "update": "new"
        }
        self.file_handler.update_json(update_)
        self.assertEqual(self.file_handler.file_content, {**json_, **update_})
        self.file_handler.close_file()

    def test_csv(self):
        self.file_handler.close_file()
        self.file_handler = FileHandler('./tests/results/test_file_handler.csv')
        csv_ = [
            ["test", "check"],
            ["123", "ok"],
        ]
        self.file_handler.write_to_file(csv_)
        file_content = list(filter(lambda x: bool(x), self.file_handler.file_content))
        self.assertEqual(file_content, csv_)
        self.file_handler.close_file()

    def test_yaml(self):
        self.file_handler.close_file()
        self.file_handler = FileHandler('./tests/results/test_file_handler.yaml')
        yaml_ = {
            "test": "123",
            "check": "ok",
        }
        self.file_handler.write_to_file(yaml_)
        file_content = self.file_handler.file_content
        self.assertEqual(file_content, yaml_)
        self.file_handler.close_file()

    def test_pickle(self):
        self.file_handler.close_file()
        self.file_handler = FileHandler('./tests/results/test_file_handler.pickle')
        pickle_ = {
            "test": 123,
            "check": "ok",
        }
        self.file_handler.write_to_file(pickle_)
        file_content = self.file_handler.file_content
        self.assertEqual(file_content, pickle_)
        self.file_handler.close_file()

    def test_toml(self):
        self.file_handler.close_file()
        self.file_handler = FileHandler('./tests/results/test_file_handler.toml')
        toml_ = {
            "test": "123",
            "check": "ok",
        }
        self.file_handler.write_to_file(toml_)
        file_content = self.file_handler.file_content
        self.assertEqual(file_content, toml_)
        self.file_handler.close_file()

    def test_html(self):
        self.file_handler.close_file()
        self.file_handler = FileHandler('./tests/results/test_file_handler.html')
        html_ = "<html><body><h1>Test</h1></body></html>"
        self.file_handler.write_to_file(html_)
        file_content = self.file_handler.file_content
        self.assertEqual(file_content, html_)
        self.file_handler.close_file()

    def test_clear_file(self):
        try:
            self.file_handler.clear_file()
            self.assertTrue(self.file_handler.file_content == '')
        except Exception as e:
            self.fail(e.__str__())

    def test_delete_file(self):
        try:
            prev_path = self.file_handler.filepath
            self.file_handler.delete_file()
            self.assertFalse(os.path.exists(prev_path))
            self.file_handler.open_file()
        except Exception as e:
            self.fail(e.__str__())
    

if "__name__" == "__main__":
    unittest.main()