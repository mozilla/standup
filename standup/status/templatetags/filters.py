from urllib.parse import urlencode

from django_jinja import library
from soapbox.models import Message


@library.global_function
def get_messages_for_page(request):
    if request.path_info:
        return Message.objects.match(request.path_info)

    return []


@library.global_function
def merge_query(request, **kwargs):
    """merge query params into existing ones"""
    params = request.GET.dict()
    params.update(kwargs)
    return urlencode(params)


@library.filter
def dateformat(date, fmt='%Y-%m-%d'):
    def suffix(d):
        suffixes = {1: 'st', 2: 'nd', 3: 'rd'}
        return 'th' if 11 <= d <= 13 else suffixes.get(d % 10, 'th')

    return date.strftime(fmt).replace('{S}', str(date.day) + suffix(date.day))
