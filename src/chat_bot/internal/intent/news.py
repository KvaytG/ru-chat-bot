import os
import aiohttp
import feedparser
from dotenv import load_dotenv

load_dotenv()

_URL = "https://ria.ru/export/rss2/archive/index.xml"
PROXY_URL = os.getenv("PROXY_URL")


async def get_news(session: aiohttp.ClientSession, limit: int = 5) -> str:
    """ INTERNAL FUNCTION! """
    try:
        async with session.get(_URL, proxy=PROXY_URL) as response:
            if response.status != 200:
                return f"К сожалению, мне не удалось узнать новости. Код ошибки: {response.status}."
            xml_data = await response.text()
        feed = feedparser.parse(xml_data)
        if not feed.entries:
            return "К сожалению, новостей не найдено или лента пуста."
        result = [f"<b>РИА новости</b>\n"]
        for i, entry in enumerate(feed.entries[:limit], 1):
            title = entry.title.strip()
            link = entry.link
            result.append(f'{i}. <a href="{link}">{title}.</a>')
        return "\n".join(result)
    except Exception as e:
        return f"К сожалению, произошла ошибка: {e}"
