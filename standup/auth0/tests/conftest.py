from django.contrib import messages
from django.contrib.messages import api as messages_api
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.cache import cache
from django.test.client import RequestFactory

import pytest


def pytest_runtest_setup(item):
    # Clear the cache before every test
    cache.clear()


class BetterRequestFactory(RequestFactory):
    """RequestFactory that *does* run session and messages middleware"""
    def _middlewarify(self, req):
        for cls in (
                SessionMiddleware,
                MessageMiddleware
        ):
            middleware = cls()
            middleware.process_request(req)

        req.session.save()

    def get(self, *args, **kwargs):
        req = super().get(*args, **kwargs)
        self._middlewarify(req)
        return req

    def post(self, *args, **kwargs):
        req = super().get(*args, **kwargs)
        self._middlewarify(req)
        return req


@pytest.fixture
def request_factory():
    """Returns a request factory that has session and messages support"""
    return BetterRequestFactory()


class MessagesCatcher:
    def __init__(self):
        self.messages = []
        self._add_message = None
        self._api_add_message = None

    def add_message(self, request, level, message, extra_tags='', fail_silently=False):
        self.messages.append({
            'request': request,
            'level': level,
            'message': message,
            'extra_tags': extra_tags,
            'fail_silently': fail_silently
        })

    def get_messages(self):
        return self.messages

    def __enter__(self):
        if self._add_message is not None:
            raise Exception('Already in a context.')

        self.messages = []
        self._add_message = messages.add_message
        messages.add_message = self.add_message
        self._api_add_message = messages_api.add_message
        messages_api.add_message = self.add_message

    def __exit__(self, exc_type, exc_value, traceback):
        messages.add_message = self._add_message
        self._add_message = None
        messages_api.add_message = self._api_add_message
        self._api_add_message = None


@pytest.yield_fixture
def messages_catcher():
    """Returns a context for capturing messages"""
    mc = MessagesCatcher()
    with mc:
        yield mc
