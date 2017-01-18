"""
WSGI config for standup project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""

import os

from django.core.cache.backends.memcached import BaseMemcachedCache
from django.core.wsgi import get_wsgi_application

from raven.contrib.django.raven_compat.middleware.wsgi import Sentry


# Fix django closing connection to MemCachier after every request (#11331)
# per the MemCachier docs.
BaseMemcachedCache.close = lambda self, **kwargs: None

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "standup.settings")

application = Sentry(get_wsgi_application())
