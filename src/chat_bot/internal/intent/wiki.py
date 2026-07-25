import asyncio
import re
import string
from wiki_search import WikiSearcher
from ..ner import ner_manager

_REDUNDANT_PUNCTUATION_PATTERN = re.compile(rf'[{re.escape(string.punctuation)}]+')
_WIKI_PATTERN = re.compile(r'(?i)\b(вики|что такое|кто такой|найди|расскажи про|расскажи мне)\b')

_searcher = WikiSearcher('kvaytg0@gmail.com')


async def get_wiki(query: str) -> str:
    """ INTERNAL FUNCTION! """
    query = _WIKI_PATTERN.sub('', query)
    query = _REDUNDANT_PUNCTUATION_PATTERN.sub('', query).strip()
    if not query:
        return 'Извините, но что именно мне нужно поискать?'
    result = await asyncio.to_thread(_searcher.search, query)
    if not result:
        subject = await asyncio.to_thread(ner_manager.get_subject, query)
        if subject:
            result = await asyncio.to_thread(_searcher.search, subject)
    if not result or not result.get('summary'):
        return f'К сожалению, я не нашёл подходящей статьи по запросу «{query}».'
    return f'<a href="{result["url"]}">{result["summary"]}</a>'
