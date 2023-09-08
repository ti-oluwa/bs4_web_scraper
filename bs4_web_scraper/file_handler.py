import os
import yaml
import toml
import json
import csv
import pickle
from typing import (IO, Dict, List, Any, Tuple)
from collections.abc import Iterable

from .exceptions import FileError



class FileHandler:
    """
    #### Handles basic read and write operations on supported file types.

    NOTE:
        On instantiation, the file object is opened in 'a+' mode and stored in the `file` attribute.
        Remember to close the file object by calling the `close_file` method when done with the file.

    #### Supported File Types:
    .csv, .json, .txt, .html, .xml, .yml, .yaml, .js, .css, .md, .toml
    .doc, .docx, .pdf, .pickle, .pkl, .log, '.htm', '.xht', '.xhtml', '.shtml' etc. Mostly text based file types.

    #### Parameters:
    @param str `filepath`: path to the file to be read or written to.

    @param str `encoding`: encoding to be used when reading or writing to the file. Defaults to 'utf-8'.

    @param bool `not_found_ok`: Whether to raise FileNotFoundError if file object specified by `filepath`
    cannot be found. If set to True, the file is created if it cannot be found and no exception is raised, otherwise,
    a FileNotFoundError is raised. Defaults to True.

    @param bool `exist_ok`: Whether to raise FileExistsError if file object specified by `filepath`
    already exists. If set to True, the already existent file is handled and no exception is raised, otherwise,
    a FileExistsError is raised. Defaults to True.

    #### Attributes:
    @attr str `filetype`: type of file to be read or written to. This is determined by the file extension.

    @attr str `filename`: name of the handled file.

    @attr IO `file`: file object to be read or written into.

    @attr str `created_file`: returns True if file was created by handler, returns False if file was existent.

    AVOID USING THE `file` ATTRIBUTE DIRECTLY. USE THE `open_file` AND `close_file` METHODS INSTEAD.
    USE THE `read_file` AND `write_to_file` METHODS TO READ AND WRITE TO THE FILE. PRIVATE METHODS ARE NOT GUARANTEED TO WORK.
    """

    _file: IO = None
    created_file: bool = False

    def __init__(
            self, 
            filepath: str, 
            encoding: str = 'utf-8', 
            not_found_ok: bool = True, 
            exists_ok: bool = True, 
            allow_any: bool = False
        ) -> None:
        self.filepath = os.path.abspath(filepath)
        self.encoding = encoding
        self.allow_any = allow_any
        
        if not os.path.exists(self.filepath):
            if not_found_ok is False:
                raise FileNotFoundError(f"File not found: {self.filepath}")
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            open(self.filepath, 'x').close()
            self.created_file = True

        else:
            if exists_ok is False:
                raise FileExistsError(f"File already exist: {self.filepath}")
        if not os.path.isfile(self.filepath):
            raise FileError(f"File not created: {self.filepath}. Check if the path points to a file.")
        # open file in append mode by default so it can be written into and read from 
        # even if the `open_file` method has not being called yet.
        self.open_file('a+')


    def __str__(self) -> str:
        return self.read_file()

    def __exit__(self, exc_type, exc_value, traceback):
        self.close_file()

    @property
    def file(self):
        return self._file

    @property
    def filetype(self) -> str:
        filetype = os.path.splitext(self.filepath)[-1].removeprefix('.').lower()
        if filetype in ['yaml', 'yml']:
            filetype = 'yaml'
        elif filetype in ['pickle', 'pkl']:
            filetype = 'pickle'
        return filetype

    @property
    def filename(self) -> str:
        filename = self.filepath.replace(os.path.dirname(self.filepath), '')
        return filename.replace('\\', '')
    
    @property
    def file_content(self):
        content = self.read_file('r')
        self.close_file()
        return content


    @staticmethod
    def supported_file_types() -> Tuple[str]:
        return (
        'txt', 'doc', 'docx', 'pdf', 'html', 'htm', 'xml',
         'js', 'css', 'md', 'json', 'csv', 'yaml', 'yml', 
         'toml', 'pickle', 'pkl', 'log', 'xht', 'xhtml', 'shtml',
        )


    def open_file(self, mode: str = 'a+') -> IO:
        '''
        Opens the file in the specified mode. Default mode is 'a+'.
        
        Args:
            mode (str): The mode to open the file in. Default is 'a+'
        '''
        try:
            self.close_file()
        except Exception:
            pass
        try:
            if 'b' in mode:
                self._file = open(self.filepath, mode=mode)
            else:
                self._file = open(self.filepath, mode=mode, encoding=self.encoding)
            return self.file
        except Exception as e:
            raise FileError(f"File cannot be opened. {e}")


    def close_file(self) -> None:
        '''
        Closes the file.
        '''
        if self.file:
         return self.file.close()
        return None


    def clear_file(self):
        """
        Empties file.

        Returns the file open in the mode it was being used in before clearing was done.
        """
        im_ = self.file.mode
        self.open_file('w')
        self.file.write('')
        # Opens the file using mode before the the file was cleared to ensure that the file is 
        # still available for use in the initial user preferred mode
        return self.open_file(im_)


    def delete_file(self):
        '''Deletes the file.'''
        try:
            self.close_file()
            os.remove(self.filepath)
            self._file = None
            self.file_path = None
        except Exception as e:
            raise FileError(f"File could not be deleted. {e}")


    def copy_to(self, destination: str):
        '''
        Copies the file to the specified destination.

        Returns a new FileHandler object for the destination file.

        Args:
            destination (str): The path to the directory where the file will be copied to.
        '''
        # check if destination is a file or directory
        if not os.path.splitext(destination)[1]: # is directory
            hdl = FileHandler(f'{destination}/{self.filename}', encoding=self.encoding)
        else:
            hdl = FileHandler(destination, encoding=self.encoding)
        hdl.write_to_file(self.read_file(), write_mode='w+')
        self.close_file()
        return hdl


    def move_to(self, destination: str) -> None:
        '''
        Moves the file to the specified destination. `self.file` becomes the destination file.

        NOTE: The handler automatically switches to handling the destination file as the
        previous file no longer exists after it has been moved

        Args:
            destination (str): The path to the directory where the file will be moved to.
        '''
        try:
            dst_hdl = self.copy_to(destination)
            self.delete_file()
            self._file = dst_hdl.file
            self.filepath = dst_hdl.filepath
            return None
        except Exception as e:
            raise FileError(f"File could not be moved. {e}")
    

    def read_file(self, read_mode: str | None = None) -> Any:
        '''
        Reads the file and returns the content using the specified `read_mode`.

        Args:
            read_mode(str): The mode to be used to read the file. If None, it reads in 'read(r+)' mode.
        '''
        if read_mode and read_mode in ['w', 'wb', 'a', 'ab']:
            raise FileError(f"`{read_mode}` mode does not allow reading from file")

        if self.filetype in self.supported_file_types() or self.allow_any is True:
            self.open_file(read_mode or 'r+')
            try:
                return getattr(self, f'_read_{self.filetype}')()
            except AttributeError:
                return self.file.read()
        raise FileError(F"Unsupported File Type: `{self.filetype}`")

    
    def write_to_file(self, content: Any, write_mode: str | None = None):
        '''
        Writes the content to the file using the specified `write_mode`.

        NOTE: This method will always replace JSON file content with new content.
        To update the JSON file use the `update_json` method.

        Args:
            content (Any): The content to write to the file.
            write_mode(str): The mode to be used to write the file. If None, it writes in append(a+) mode.
            To overwrite previous content set as 'w' or 'wb'.
        '''
        if write_mode and write_mode in ['r', 'rb']:
            raise FileError(f"`{write_mode}` mode does not allow writing to file")

        if self.filetype in self.supported_file_types() or self.allow_any is True:
            self.open_file(write_mode or 'a+')
            self._write_content(content)
            return self.close_file()
        raise FileError(F"Unsupported File Type: `{self.filetype}`")


    def _write_content(self, content: Any):
        try:
            return getattr(self, f'_write_{self.filetype}')(content)
        except AttributeError:
            self.file.write(content)
        return None
            

    def _read_json(self) -> Dict:
        '''
        Reads the file and returns the content as a dictionary.
        '''
        try:
            return json.load(self.file)
        except Exception as e:
            raise FileError(f'JSON file could not be loaded. {e}')


    def _write_json(self, content: Dict, indent: int = 4) -> None:
        '''
        Writes new content to file after clearing previous content.

        Args:
            content (Dict): JSON serializable content to write to the file
        '''
        if not isinstance(content, dict):
            raise TypeError('Invalid type for `content`')
        try:
            self.clear_file()
            _json = json.dumps(content, indent=indent)
            return self.file.write(_json)
        except Exception as e:
            raise FileError(f'File cannot be written into. {e}')

    
    def update_json(self, content: Dict):
        """
        Updates the content of JSON file with new content dict.

        Args::
            content (Dict): JSON serializable content to update the file with.
        """
        if self.filetype == 'json':
            try:
                file_cnt = self.read_file()
            except:
                file_cnt = {}
            file_cnt.update(content)
            return self.write_to_file(file_cnt, 'w')
        raise FileError(f"`update_json` cannot be used on '{self.filetype}' files.")


    def _write_csv(self, content: Iterable[Iterable]) -> None:
        '''
        Writes the content to the file.

        Args:
            content (List | Tuple): The content to write to the file
        '''
        if not isinstance(content, Iterable):
            raise TypeError("Invalid type for `content`")
        writer = csv.writer(self.file)
        writer.writerows(content)
        return None


    def _read_csv(self) -> List:
        '''
        Reads the file and returns the content as a list.
        '''
        try:
            reader = csv.reader(self.file)
            return list(reader)
        except Exception as e:
            raise FileError(f'csv file could not be read. {e}')


    def _read_yaml(self) -> Dict: #
        '''
        Reads the file and returns the content as a dictionary.
        '''
        try:
            return yaml.load(self.file, Loader=yaml.FullLoader)
        except Exception as e:
            raise FileError(f'yaml file could not be loaded. {e}')

    
    def _write_yaml(self, content: dict) -> None: #
        '''
        Writes the content to the file.

        Args:
            content (dict): The content to write to the file
        '''
        yaml.dump(
            content, self.file, 
            default_flow_style=False, 
            encoding=self.encoding
        )
        return None


    def _read_pickle(self) -> Any:
        '''
        Reads the file and returns the content.
        '''
        try:
            self.open_file('rb+')
            return pickle.load(self.file)
        except Exception as e:
            raise FileError(f'pickle file could not be loaded. {e}')


    def _write_pickle(self, content: Any) -> None:
        '''
        Writes the content to the file.

        Args:
            content (Any): The content to write to the file
        '''
        # pkl = pickle.dumps(content).decode(self.encoding)
        # self.file.write(pkl)
        self.open_file('ab+')
        pickle.dump(content, self.file)
        return None


    def _read_toml(self) -> Dict:
        '''
        Reads the file and returns the content as a dictionary.
        '''
        try:
            return toml.load(self.file)
        except Exception as e:
            raise FileError(f'toml file could not be loaded. {e}')


    def _write_toml(self, content: dict) -> None:
        '''
        Writes the content to the file.

        Args:
            content (dict): The content to write to the file
        '''
        toml.dump(content, self.file)
        return None


