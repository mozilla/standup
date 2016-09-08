"""
Register functions from django-browserid since we don't use Jinjo
"""
from django_browserid.helpers import (
    browserid_info,
    browserid_js,
    browserid_login,
    browserid_logout,
)
from django_jinja import library


library.global_function(browserid_info)
library.global_function(browserid_js)
library.global_function(browserid_login)
library.global_function(browserid_logout)
