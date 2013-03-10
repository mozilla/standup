import os

from standup.utils import truthify

# Application settings.
# To override the values, create a local_settings.py and enter the
# new values there.

DEBUG = truthify(os.environ.get('DEBUG', False))

# The key used to authenticate API calls.
API_KEY = os.environ.get('API_KEY', 'qwertyuiopasdfghjklzxcvbnm1234567890')

INSTALLED_APPS = (
    'api',
    'api2',
    'landings',
    'status',
    'users'
)

SITE_URL = os.environ.get('SITE_URL', 'http://127.0.0.1:5000')
SITE_TITLE = os.environ.get('SITE_TITLE', 'standup')

SESSION_SECRET = os.environ.get('SESSION_SECRET',
                                'asdfghjklqwertyuiopzxcvbnm1234567890')

DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///standup_app.db')

# Flask-Funnel settings
LESS_PREPROCESS = truthify(os.environ.get('LESS_PREPROCESS', False))
JAVA_BIN = os.environ.get('JAVA_BIN', 'java')
YUI_COMPRESSOR_BIN = os.environ.get('YUI_COMPRESSOR_BIN', os.path.realpath(
    os.path.join(os.path.dirname(__file__), '..', 'bin',
                 'yuicompressor-2.4.7.jar')))

try:
    from bundles import *
except ImportError:
    pass

try:
    from local_settings import *
except ImportError:
    pass
