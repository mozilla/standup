from django.core.cache import cache


def pytest_runtest_setup(item):
    # Clear the cache before every test
    cache.clear()
