import os
import sys
from pathlib import Path

from everett.manager import ConfigManager, ConfigEnvFileEnv, ConfigOSEnv, ListOf
import dj_database_url


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
SITE_TITLE = config('SITE_TITLE', default='standup')

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

    'standup.api',
    'standup.status',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
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

WSGI_APPLICATION = 'standup.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': config('DATABASE_URL',
                      parser=dj_database_url.parse,
                      default='sqlite:///db.sqlite3')
}


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

SECURE_BROWSER_XSS_FILTER = config('SECURE_BROWSER_XSS_FILTER', default='true', parser=bool)
# this should be 31536000 in prod (1 year)
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default='0', parser=int)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default='false', parser=bool)

GRAVATAR_DEFAULT_IMAGE = 'http://www.standu.ps/static/img/default-avatar.png'
GRAVATAR_DEFAULT_SECURE = False

LOGIN_URL = '/'


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_ROOT = path('staticfiles')
STATIC_URL = '/static/'
STATICFILES_STORAGE = 'standup.status.storage.StandupStorage'
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'pipeline.finders.PipelineFinder',
)

PIPELINE = {
    'STYLESHEETS': {
        'common': {
            'source_filenames': (
                'css/normalize.css',
                'less/style.less',
            ),
            'output_filename': 'css/common.min.css',
        },
        'profile': {
            'source_filenames': (
                'less/profile.less',
            ),
            'output_filename': 'css/profile.min.css',
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
        'modernizr': {
            'source_filenames': (
                'js/vendor/modernizr-2.6.1.js',
            ),
            'output_filename': 'js/modernizr.min.js',
        }
    },
    'DISABLE_WRAPPER': True,
    'SHOW_ERRORS_INLINE': False,
    'COMPILERS': (
        'pipeline.compilers.less.LessCompiler',
    ),
    'LESS_BINARY': config('PIPELINE_LESS_BINARY',
                          default=path('node_modules', '.bin', 'lessc')),
    # 'LESS_ARGUMENTS': config('PIPELINE_LESS_ARGUMENTS', default='-s'),
    'JS_COMPRESSOR': 'pipeline.compressors.yuglify.YuglifyCompressor',
    'CSS_COMPRESSOR': 'pipeline.compressors.yuglify.YuglifyCompressor',
    'YUGLIFY_BINARY': config('PIPELINE_YUGLIFY_BINARY',
                             default=path('node_modules', '.bin', 'yuglify')),
}

if sys.argv[0].endswith('py.test'):
    # won't barf if staticfiles are missing
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
