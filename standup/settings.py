# Application settings.
# To override the values, create a local_settings.py and enter the
# new values there.

# The key used to authenticate API calls.
API_KEY = 'qwertyuiopasdfghjklzxcvbnm1234567890'
DEBUG = False

try:
    from local_settings import *
except ImportError:
    pass
