"""
Voice service abstract class
"""


class Translator(object):
    # please use https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes to specify language
    def translate(self, query: str, from_lang: str = "", to_lang: str = "en") -> str:
        """
        Translate text from one language to another
        """
        raise NotImplementedError
