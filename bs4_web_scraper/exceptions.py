
class InvalidURLError(Exception):
    """URL is not valid"""
    message = "Invalid URL"

    def __init__(self, message: str = None) -> None:
        if self.message:
            self.message = message
    
    def __str__(self):
        return self.message if self.message else self.__doc__


class InvalidScrapableTagError(Exception):
    """Invalid syntax for scrapable tag"""
    message = "Invalid scrapable tag!"

    def __init__(self, message: str = None) -> None:
        if self.message:
            self.message = message

    def __str__(self):
        return self.message if self.message else self.__doc__


class FileError(Exception):
    """File handling error"""
    message = "File error! Invalid file type."

    def __init__(self, message: str = None) -> None:
        if self.message:
            self.message = message

    def __str__(self):
        return self.message if self.message else self.__doc__


class TranslationError(Exception):
    """Error encountered during translation"""
    message = "Error occurred during translation"

    def __init__(self, message: str = None) -> None:
        if message:
            self.message = message 

    def __str__(self):
        return self.message if self.message else self.__doc__


class UnsupportedLanguageError(TranslationError):
    """Language cannot be translated by translation engine"""
    message = 'Language cannot be translated by translation engine'

    def __init__(self, message: str = None, code: str = None, translation_engine: str = None) -> None:
        msg_ = ''
        if code and translation_engine:
            msg_ = f"Translation in {code} is not supported by {translation_engine}"
        elif code and not translation_engine:
            msg_ = f"Translation in {code} is not supported by translation engine"
        elif not code and translation_engine:
            msg_ = f"Language cannot be translated by {translation_engine}"
        message = f"{message}. {msg_}" if msg_ else message
        return super().__init__(message)
