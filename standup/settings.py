import sys
from pathlib import Path

from everett.manager import ConfigManager, ConfigEnvFileEnv, ConfigOSEnv, ListOf
import dj_database_url
import django_cache_url


ROOT_PATH = Path(__file__).resolve().parents[1]


def path(*paths):
    return str(ROOT_PATH.joinpath(*paths))


config = ConfigManager([
    ConfigEnvFileEnv(path('.env')),
    ConfigOSEnv(),
])


# Build paths inside the project like this: path(...)
BASE_DIR = str(ROOT_PATH)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default='false', parser=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', parser=ListOf(str), default='localhost')
ENFORCE_HOSTNAME = config('ENFORCE_HOSTNAME', parser=ListOf(str), raise_error=False)
SITE_TITLE = config('SITE_TITLE', default='Standup')

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'django_jinja',
    'django_jinja.contrib._humanize',
    'django_jinja_markdown',
    'pipeline',
    'django_gravatar',
    'raven.contrib.django.raven_compat',

    'standup.api',
    'standup.status',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'standup.status.middleware.EnforceHostnameMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'csp.middleware.CSPMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',
    'standup.status.middleware.NewUserProfileMiddleware',
)

ROOT_URLCONF = 'standup.urls'

_CONTEXT_PROCESSORS = [
    'django.template.context_processors.debug',
    'django.template.context_processors.request',
    'django.template.context_processors.static',
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
    'standup.status.context_processors.status',
]

TEMPLATES = [
    {
        'BACKEND': 'django_jinja.backend.Jinja2',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            # Use jinja2/ for jinja templates
            'app_dirname': 'jinja2',
            # Don't figure out which template loader to use based on
            # file extension
            'match_extension': '',
            'newstyle_gettext': True,
            'context_processors': _CONTEXT_PROCESSORS,
            # 'undefined': 'jinja2.StrictUndefined',
            'extensions': [
                'jinja2.ext.do',
                'jinja2.ext.i18n',
                'jinja2.ext.loopcontrols',
                'jinja2.ext.with_',
                'jinja2.ext.autoescape',
                'pipeline.jinja2.PipelineExtension',
                'django_gravatar.jinja2.GravatarExtension',
                'django_jinja.builtins.extensions.CsrfExtension',
                'django_jinja.builtins.extensions.DjangoFiltersExtension',
                'django_jinja.builtins.extensions.StaticFilesExtension',
                'django_jinja.builtins.extensions.UrlsExtension',
                'django_jinja_markdown.extensions.MarkdownExtension',
            ],
        }
    },
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': _CONTEXT_PROCESSORS,
        },
    },
]
DEFAULT_JINJA2_TEMPLATE_EXTENSION = '.html'

WSGI_APPLICATION = 'standup.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': config('DATABASE_URL',
                      parser=dj_database_url.parse,
                      default='sqlite:///db.sqlite3')
}

CACHES = {
    'default': config('CACHE_URL',
                      parser=django_cache_url.parse,
                      default='locmem:default')
}
if CACHES['default'].get('BACKEND', '') == 'django.core.cache.backends.locmem.LocMemCache':
    # If we're using locmem, set timeout for 60 seconds and restrict
    # cache to 100 things so as to not run rampant with memory usage.
    CACHES['default']['timeout'] = 60
    CACHES['default'].setdefault('OPTIONS', {})['MAX_ENTRIES'] = 100
CACHE_MIDDLEWARE_SECONDS = config('CACHE_MIDDLEWARE_SECONDS', default='30', parser=int)
CACHE_FEEDS_SECONDS = config('CACHE_FEEDS_SECONDS', default='1800', parser=int)  # 30 min


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

ROBOTS_ALLOW = config('ROBOTS_ALLOW', default='false', parser=bool)

# security
SECURE_CONTENT_TYPE_NOSNIFF = config('SECURE_CONTENT_TYPE_NOSNIFF', default='true', parser=bool)
SECURE_BROWSER_XSS_FILTER = config('SECURE_BROWSER_XSS_FILTER', default='true', parser=bool)
# this should be 31536000 in prod (1 year)
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default='0', parser=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS',
                                        default='false', parser=bool)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default='false', parser=bool)
SECURE_SSL_HOST = config('SECURE_SSL_HOST', raise_error=False) or None
SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = SECURE_SSL_REDIRECT

# must be a full publicly accessible URL, or a name of a gravatar default theme
GRAVATAR_DEFAULT_IMAGE = config('GRAVATAR_DEFAULT_IMAGE', default='mm')
GRAVATAR_DEFAULT_SECURE = SECURE_SSL_REDIRECT
if GRAVATAR_DEFAULT_SECURE:
    gravatar_domain = 'secure.gravatar.com'
else:
    gravatar_domain = 'www.gravatar.com'

HELP_FAQ_URL = config('HELP_FAQ_URL', raise_error=False)

# auth
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)

AUTH0_CLIENT_ID = config('AUTH0_CLIENT_ID')
AUTH0_CLIENT_SECRET = config('AUTH0_CLIENT_SECRET')
AUTH0_DOMAIN = config('AUTH0_DOMAIN')
AUTH0_CALLBACK_URL = config('AUTH0_CALLBACK_URL')
AUTH0_PATIENCE_TIMEOUT = config('AUTH0_PATIENCE_TIMEOUT', default='5', parser=int)

# CSP
CSP_DEFAULT_SRC = (
    "'none'",
)
CSP_OBJECT_SRC = (
    "'none'",
)
CSP_BASE_URI = (
    "'self'",
)
CSP_STYLE_SRC = (
    "'self'",
    # because projects can set custom colors which happen
    # in inline style attributes. we should fix that.
    "'unsafe-inline'",
)
CSP_FONT_SRC = (
    "'self'",
)
CSP_FORM_ACTION = (
    "'self'",
    AUTH0_DOMAIN,
)
CSP_CONNECT_SRC = (
    "'self'",
    AUTH0_DOMAIN,
)
CSP_SCRIPT_SRC = (
    "'self'",
)
CSP_IMG_SRC = (
    "'self'",
    'data:',
    gravatar_domain,
    'cdn.auth0.com',
)
# should really just be child-src as frame-src is deprecated,
# but certain browsers (eyes safari) don't support connect-src.
CSP_FRAME_SRC = (
)
CSP_FRAME_ANCESTORS = (
    '*.mozilla.org',
)
CSP_REPORT_ONLY = config('CSP_REPORT_ONLY', default='false', parser=bool)
CSP_REPORT_ENABLE = config('CSP_REPORT_ENABLE', default='false', parser=bool)
if CSP_REPORT_ENABLE:
    CSP_REPORT_URI = config('CSP_REPORT_URI', default='/csp-violation-capture')

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_ROOT = path('staticfiles')
STATIC_URL = '/static/'
STATICFILES_STORAGE = 'standup.status.storage.StandupStorage'
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'pipeline.finders.PipelineFinder',
)
WHITENOISE_ROOT = path('root_files')

PIPELINE = {
    'STYLESHEETS': {
        'common': {
            'source_filenames': (
                'css/normalize.css',
                'less/style.less',
            ),
            'output_filename': 'css/common.min.css',
        },
        'user': {
            'source_filenames': (
                'less/user.less',
            ),
            'output_filename': 'css/user.min.css',
        },
    },
    'JAVASCRIPT': {
        'common': {
            'source_filenames': (
                'js/vendor/jquery-3.1.0.js',
                'js/standup.js',
            ),
            'output_filename': 'js/common.min.js',
        },
        'signin': {
            'source_filenames': (
                'js/vendor/jquery-3.1.0.js',
                'js/vendor/lock-passwordless-2.2.min.js',
                'js/standup.js',
                'js/signin.js',
            ),
            'output_filename': 'js/common.min.js',
        },
        'modernizr': {
            'source_filenames': (
                'js/vendor/modernizr-2.6.1.js',
            ),
            'output_filename': 'js/modernizr.min.js',
        },
    },
    'DISABLE_WRAPPER': True,
    'SHOW_ERRORS_INLINE': False,
    'COMPILERS': (
        'pipeline.compilers.less.LessCompiler',
    ),
    'LESS_BINARY': config('PIPELINE_LESS_BINARY',
                          default=path('node_modules', '.bin', 'lessc')),
    # 'LESS_ARGUMENTS': config('PIPELINE_LESS_ARGUMENTS', default='-s'),
    'JS_COMPRESSOR': 'pipeline.compressors.uglifyjs.UglifyJSCompressor',
    'CSS_COMPRESSOR': 'standup.pipeline.CleanCSSCompressor',
    'CLEANCSS_BINARY': config('PIPELINE_CLEANCSS_BINARY',
                              default=path('node_modules', '.bin', 'cleancss')),
    'UGLIFYJS_BINARY': config('PIPELINE_UGLIFYJS_BINARY',
                              default=path('node_modules', '.bin', 'uglifyjs')),
}

RAVEN_CONFIG = {
    'dsn': config('SENTRY_DSN', raise_error=False),
    'release': config('GIT_SHA', raise_error=False),
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': config('DJANGO_LOG_LEVEL', default='INFO'),
        },
    },
}


if sys.argv[0].endswith('py.test'):
    # won't barf if staticfiles are missing
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
    CACHES['default'] = django_cache_url.parse('dummy:')
