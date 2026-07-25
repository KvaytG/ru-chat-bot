import re

_NON_BREAKING_SPACES_PATTERN = re.compile(r'[\u202f\u00a0]')
_ZERO_WIDTH_CHARS_PATTERN = re.compile(r'[\u200b-\u200d\uFEFF]')
_DASHES_PATTERN = re.compile(r'[-—–]')
_PUNCTUATION_PATTERN = re.compile(r'[^\w\s]')
_SPACE_PATTERN = re.compile(r'\s+')


def preprocess_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower().replace('ё', 'е')
    text = _NON_BREAKING_SPACES_PATTERN.sub(' ', text)
    text = _ZERO_WIDTH_CHARS_PATTERN.sub('', text)
    text = _DASHES_PATTERN.sub(' ', text)
    text = _PUNCTUATION_PATTERN.sub('', text)
    text = _SPACE_PATTERN.sub(' ', text)
    return text.strip()
