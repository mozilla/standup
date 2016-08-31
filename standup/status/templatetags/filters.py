from django_jinja import library

from standup.status.utils import (
    dateformat,
    format_update,
)


# Register template filters
dateformat = library.filter(dateformat)
format_update = library.filter(format_update)

print('registered filters')
