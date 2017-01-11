from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
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
    return BetterRequestFactory()
