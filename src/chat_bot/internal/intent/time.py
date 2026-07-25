from ..date import get_moscow_now


def get_time() -> str:
    """ INTERNAL FUNCTION! """
    return get_moscow_now().strftime('%H:%M')
