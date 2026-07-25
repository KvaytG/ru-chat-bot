from ..date import get_moscow_now, format_date


def get_date() -> str:
    """ INTERNAL FUNCTION! """
    return format_date(get_moscow_now())
