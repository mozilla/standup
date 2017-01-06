from urllib.parse import quote_plus

from django.conf import settings


def is_auth0_configured():
    return (
        settings.AUTH0_CLIENT_ID and
        settings.AUTH0_CLIENT_SECRET and
        settings.AUTH0_DOMAIN and
        settings.AUTH0_CALLBACK_URL
    )


def build_auth0_url(request):
    # https://auth0.com/docs/client-auth/server-side-web#calling-the-authorization-url
    return settings.AUTH0_LOGIN_URL.format(
        AUTH0_DOMAIN=settings.AUTH0_DOMAIN,
        AUTH0_CLIENT_ID=quote_plus(settings.AUTH0_CLIENT_ID),
        AUTH0_CALLBACK_URL=quote_plus(settings.AUTH0_CALLBACK_URL),
        # FIXME(willkg): This should be a token that ties both ends.
        STATE='foo',
    )


def auth0(request):
    ret = {
        'auth0configured': is_auth0_configured(),
    }
    if is_auth0_configured():
        ret['auth0loginurl'] = build_auth0_url(request)
    return ret
