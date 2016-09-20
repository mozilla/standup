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
    'social.apps.django_app.default',
    'django_browserid',

    'standup.api',
    'standup.status',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'standup.status.middleware.NewUserProfileMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',    
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'social.apps.django_app.middleware.SocialAuthExceptionMiddleware',
)

ROOT_URLCONF = 'standup.urls'

_CONTEXT_PROCESSORS = [
    'django.template.context_processors.debug',
    'django.template.context_processors.request',
    'django.template.context_processors.static',
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
    'standup.status.context_processors.status',
    'social.apps.django_app.context_processors.backends',
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

# security

SECURE_BROWSER_XSS_FILTER = config('SECURE_BROWSER_XSS_FILTER', default='true', parser=bool)
# this should be 31536000 in prod (1 year)
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default='0', parser=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS',
                                        default='false', parser=bool)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default='false', parser=bool)
SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = SECURE_SSL_REDIRECT

# must be a full publicly accessible URL, or a name of a gravatar default theme
GRAVATAR_DEFAULT_IMAGE = config('GRAVATAR_DEFAULT_IMAGE', default='mm')
GRAVATAR_DEFAULT_SECURE = SECURE_SSL_REDIRECT

HELP_FAQ_URL = config('HELP_FAQ_URL', raise_error=False)

# auth
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'django_browserid.auth.BrowserIDBackend',
    'social.backends.github.GithubOAuth2',
)
BROWSERID_AUDIENCES = config('BROWSERID_AUDIENCES',
                             default='http://localhost:8000,'
                                     'http://www.standu.ps,'
                                     'http://standupstage.herokuapp.com',
                             parser=ListOf(str))
BROWSERID_REQUEST_ARGS = {
    'siteName': SITE_TITLE,
}
BROWSERID_CREATE_USER = 'standup.status.auth.browserid_create_user'
LOGIN_URL = '/'
LOGOUT_URL = '/logout/'
LOGIN_REDIRECT_URL = '/'
LOGIN_REDIRECT_URL_FAILURE = '/'
SOCIAL_AUTH_LOGIN_ERROR_URL = '/'
SOCIAL_AUTH_NEW_USER_REDIRECT_URL = '/profile/'
SOCIAL_AUTH_ADMIN_USER_SEARCH_FIELDS = ['username', 'first_name', 'last_name', 'email']
SOCIAL_AUTH_GITHUB_KEY = config('SOCIAL_AUTH_GITHUB_KEY', raise_error=False)
SOCIAL_AUTH_GITHUB_SECRET = config('SOCIAL_AUTH_GITHUB_SECRET', raise_error=False)
SOCIAL_AUTH_GITHUB_SCOPE = ['user:email']
# from social/pipeline/__init__.py
SOCIAL_AUTH_PIPELINE = (
    'social.pipeline.social_auth.social_details',
    'social.pipeline.social_auth.social_uid',
    'social.pipeline.social_auth.social_user',
    'social.pipeline.user.get_username',
    # uncomment the following for debug output
    # 'social.pipeline.debug.debug',
    'social.pipeline.social_auth.associate_by_email',
    'social.pipeline.user.create_user',
    'standup.status.auth.create_user_profile',
    'social.pipeline.social_auth.associate_user',
    'social.pipeline.social_auth.load_extra_data',
    'social.pipeline.user.user_details'
)


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
        'browserid': {
            'source_filenames': (
                'browserid/persona-buttons.css',
            ),
            'output_filename': 'css/browserid.min.css',
        }
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
        },
        'browserid': {
            'source_filenames': (
                'browserid/api.js',
                'browserid/browserid.js',
            ),
            'output_filename': 'js/browserid.min.js',
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
