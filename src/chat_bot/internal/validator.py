import re
import string

_RUSSIAN_PATTERN = re.compile(fr"^[а-яА-ЯёЁ\s\d{re.escape(string.punctuation + '–«»')}]+$")


def is_valid_text(text: str) -> bool:
    """ INTERNAL FUNCTION! """
    return bool(_RUSSIAN_PATTERN.match(text))
