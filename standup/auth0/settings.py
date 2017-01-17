from collections import OrderedDict
from collections.abc import Sequence
from textwrap import dedent

from django.conf import settings


class NoValue:
    def __nonzero__(self):
        return False

    def __bool__(self):
        return False

    def __repr__(self):
        return 'NO VALUE'


NO_VALUE = NoValue()


class ConfigurationError(Exception):
    pass


class Option:
    def __init__(self, key, default=NO_VALUE, parser=str, help_text=''):
        self.key = key
        self.default = default
        self.parser = parser
        self.help_text = help_text


def list_of_str(val):
    """Returns a list of strings"""
    val = val or []
    if isinstance(val, str):
        val = val.split(',')

    # Assert it's a sequence
    assert isinstance(val, Sequence), 'Not a sequence'
    val = list(val)

    # Assert it's a sequence of strings
    non_strings = [item for item in val if not isinstance(item, str)]
    assert not non_strings, 'Some values are not strings %r' % non_strings
    return val


class AppSettings:
    _all_options = [
        Option(
            'AUTH0_CLIENT_ID',
            help_text='Your Auth0 client id. This is public-ish.'
        ),
        Option(
            'AUTH0_CLIENT_SECRET',
            help_text=dedent("""\
            Your Auth0 client secret. This is **NOT** public. Do not put this
            in version control, print it out anywhere, put it in your templates,
            log it, send it in a postcard to your boss, put it on a t-shirt,
            etc.
            """)
        ),
        Option(
            'AUTH0_DOMAIN',
            help_text=dedent("""\
            Domain for Auth0 login page.

            For example, I set up an app with Auth0 and the domain they gave me is
            ``willkg.auth0.com``.

            Mozilla uses ``auth.mozilla.auth0.com``.
            """)
        ),
        Option(
            'AUTH0_LOGIN_URL',
            help_text=dedent("""\
            This is the complete url to the Auth0 login page. It allows for variables
            so you don't have to have things in your settings file/environment multiple
            times. It will urlencode the values.

            Variables:

            * ``AUTH0_DOMAIN`` -- from settings
            * ``AUTH0_CLIENT_ID`` -- from settings
            * ``AUTH0_CALLBACK_URL`` -- from settings
            * ``STATE`` -- generated and stored in the request session and compared
            against later in the flow

            For example, the one I use for my app is (all on one line)::

                https://{AUTH0_DOMAIN}/authorize?response_type=code&client_id={AUTH0_CLIENT_ID}
                &redirect_uri={AUTH0_CALLBACK_URL}&state={STATE}

            The one we use for Mozilla is (all on one line)::

                https://{AUTH0_DOMAIN}/login?client={AUTH0_CLIENT_ID}&protocol=oauth2&state={STATE}
                &redirect_uri={AUTH0_CALLBACK_URL}&scope=openid+email+profile&response_type=code

            Look at the Auth0 and Mozilla IAM documentation for how to set up the url.
            """)
        ),
        Option(
            'AUTH0_CALLBACK_URL',
            help_text=dedent("""\
            This is the complete url to the callback view of your app that Auth0
            will redirect to after the user has authenticated.

            It needs to be something like ``https://yourdomain/auth/login``.
            """)
        ),
        Option(
            'AUTH0_PIPELINE', parser=list_of_str,
            help_text=dedent("""\

            This is the list of transforms that get executed in order after the user has
            authenticated with Auth0. This pipeline is responsible for associating the Auth0
            identity with a Django user, rejecting certain users (inactive? no email address?),
            adding any metadata, logging the user in, creating profiles, etc.

            Pipeline transform functions are defined in ``standup/auth0/pipeline.py``.

            The order of the pipeline is important. For example, you can't have transforms that need
            to look at a user instance occur in the pipeline before the user instance has been
            acquired--it'll throw an error.

            We have a Mozilla meta pipeline that you can use:
            ``standup.auth0.pipeline.mozilla_auth0_pipeline``.
            """)
        ),
        Option(
            'AUTH0_SIGNIN_VIEW',
            help_text=dedent("""\
            The Django view name for the view of your signin page.

            For example, on Standup, we have a separate page for signing in and the
            Django view name is ``users.loginform``.

            If you have a signin link on every page in the navbar or something like
            that, then you could use the view name for the home page.

            This is used every time we need to logout a user and redirect them to a
            signin form.
            """)
        ),
        Option(
            'AUTH0_PATIENCE_TIMEOUT', default=5, parser=int,
            help_text=dedent("""\
            The amount of time in seconds that your app will wait when
            sending requests to the Auth0 server.
            """)
        ),
        Option(
            'AUTH0_ID_TOKEN_DOMAINS',
            help_text=dedent("""\
            list of strings: The domains that require an ``id_token`` for your app.

            For Mozilla sites, this is something like::

                ['mozilla.com', 'mozillafoundation.org', 'mozilla-japan.org']

            If someone logs into Auth0 using an account that has a verified email address
            with one of those domains, then they'll be required to have logged in using
            an Oauth2 Auth0 provider like the Mozilla LDAP option. If they didn't use
            such a provider, they're immediately logged out and told to use an
            appropriate provider.
            """)
        ),
        Option(
            'AUTH0_ID_TOKEN_EXPIRY', default=900, parser=int,
            help_text=dedent("""\
            Users who used an Oauth2 Auth0 provider and have a verified
            email address in ``AUTH0_ID_TOKEN_DOMAINS`` have their ``id_token`` renewed
            every ``AUTH0_ID_TOKEN_EXPIRY`` seconds.

            If the ``id_token`` fails renewal, the user is immediately logged out.
            """)
        )
    ]

    def __init__(self):
        self._option_map = OrderedDict([
            (opt.key, opt) for opt in self._all_options
        ])

    def get(self, key):
        opt = self._option_map[key]
        val = getattr(settings, opt.key, NO_VALUE)
        if val is not NO_VALUE:
            try:
                return opt.parser(val)
            except Exception:
                msg = '"%s": "%s" kicked up error when parsing.' % (opt.key, val)
                if opt.help_text:
                    msg = '%s\n\n%s' % (msg, opt.help_text)
                raise ConfigurationError(msg)

        if opt.default is not NO_VALUE:
            try:
                return opt.parser(opt.default)
            except Exception:
                msg = '"%s": "%s" (default) kicked up error when parsing.' % (opt.key, val)
                if opt.help_text:
                    msg = '%s\n\n%s' % (msg, opt.help_text)
                raise ConfigurationError(msg)

        msg = '"%s" must be configured in settings.' % opt.key
        if opt.help_text:
            msg = '%s\n\n%s' % (msg, opt.help_text)
        raise ConfigurationError(msg)

    def __getattr__(self, key):
        if key.startswith('AUTH0'):
            return self.get(key)
        super().__getattr__(self, key)


app_settings = AppSettings()
