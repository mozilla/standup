from urllib.parse import urlencode

from django_jinja import library

from standup.status.utils import (
    dateformat,
    format_update,
)


# Register template filters
dateformat = library.filter(dateformat)
format_update = library.filter(format_update)


@library.global_function
def merge_query(request, **kwargs):
    """merge query params into existing ones"""
    params = request.GET.dict()
    params.update(kwargs)
    return urlencode(params)
