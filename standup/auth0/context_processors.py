from urllib.parse import quote_plus
from uuid import uuid4

from django.conf import settings


def is_auth0_configured():
    return (
        settings.AUTH0_CLIENT_ID and
        settings.AUTH0_CLIENT_SECRET and
        settings.AUTH0_DOMAIN and
        settings.AUTH0_CALLBACK_URL
    )


class Auth0URL:
    """Class that generates an Auth0URL on demand"""
    def __init__(self, request):
        self.request = request

    def __str__(self):
        # If there isn't a session, create one now
        if not self.request.session.session_key:
            self.request.session.create()

        # Stick a "state" token in
        self.request.session['auth0_state'] = str(uuid4())

        # https://auth0.com/docs/client-auth/server-side-web#calling-the-authorization-url
        return settings.AUTH0_LOGIN_URL.format(
            AUTH0_DOMAIN=settings.AUTH0_DOMAIN,
            AUTH0_CLIENT_ID=quote_plus(settings.AUTH0_CLIENT_ID),
            AUTH0_CALLBACK_URL=quote_plus(settings.AUTH0_CALLBACK_URL),
            STATE=self.request.session['auth0_state']
        )


def auth0(request):
    ret = {
        'auth0configured': is_auth0_configured(),
    }
    if is_auth0_configured():
        ret['auth0loginurl'] = Auth0URL(request)
    return ret
