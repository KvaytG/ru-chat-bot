import os
import asyncio
import aiohttp
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from ..ner import ner_manager
from ..date import format_date, get_moscow_now

load_dotenv()

API_KEY = os.getenv("WEATHER_API_KEY")
PROXY_URL = os.getenv("PROXY_URL")


async def _get_weather_live(session: aiohttp.ClientSession, city: str, target_date=None):
    if not API_KEY:
        return "К сожалению, мне не удалось узнать погоду. Код ошибки: -1."
    now = get_moscow_now()
    if target_date and target_date.tzinfo is None:
        target_date = target_date.replace(tzinfo=ZoneInfo("Europe/Moscow"))
    if target_date and target_date.date() < now.date():
        return "К сожалению, я умею смотреть погоду только на сегодня и на ближайшие несколько дней. Узнать, что было в прошлом, я не могу."
    is_today = target_date is None or target_date.date() == now.date()
    url = "https://api.openweathermap.org/data/2.5/weather" if is_today else "https://api.openweathermap.org/data/2.5/forecast"
    params = {'q': city, 'appid': API_KEY, 'units': 'metric', 'lang': 'ru'}
    try:
        async with session.get(url, params=params, proxy=PROXY_URL) as response:
            if response.status != 200:
                return f"К сожалению, мне не удалось узнать погоду. Код ошибки: {response.status}."
            res_data = await response.json()
            if is_today:
                data = res_data
            else:
                target_ts = target_date.timestamp()
                data = min(res_data['list'], key=lambda x: abs(x['dt'] - target_ts))
            temp = round(data['main']['temp'])
            description = data['weather'][0]['description'].capitalize()
            date_str = format_date(target_date if target_date else now)
            display_city = res_data.get('name') or res_data.get('city', {}).get('name')
            return (
                f"<b>{display_city}</b> ({date_str})\n\n"
                f"<b>{description}</b>.\n\n"
                f"Температура: <b>{temp}°C</b>.\n"
                f"Влажность: <b>{data['main']['humidity']}%</b>.\n"
                f"Ветер: <b>{data['wind'].get('speed')} м/с</b>."
            )
    except Exception as e:
        return f"Произошла ошибка при запросе погоды: {e}"


async def get_weather(session: aiohttp.ClientSession, text: str) -> str:
    """ INTERNAL FUNCTION! """
    res = await asyncio.to_thread(ner_manager.analyze, text)
    city = "Москва"
    date = None
    if res:
        city = res[0].get('city') or "Москва"
        date = res[0].get('date')
    return await _get_weather_live(session, city, date)
