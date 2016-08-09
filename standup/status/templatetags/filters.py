from django_jinja import library

from standup.status.utils import (
    dateformat,
    format_update,
    gravatar_url,
)


# Register template filters
dateformat = library.filter(dateformat)
format_update = library.filter(format_update)
gravatar_url = library.filter(gravatar_url)
