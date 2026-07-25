from datetime import datetime
from zoneinfo import ZoneInfo


def get_moscow_now():
    """ INTERNAL FUNCTION! """
    return datetime.now(ZoneInfo("Europe/Moscow"))


def format_date(dt):
    """ INTERNAL FUNCTION! """
    if dt is None:
        return "сейчас"
    months = [
        "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря"
    ]
    if dt.year == get_moscow_now().year:
        return f"{dt.day} {months[dt.month - 1]}"
    return f"{dt.day} {months[dt.month - 1]} {dt.year}"
