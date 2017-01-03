from django.conf import settings


def is_auth0_configured():
    return (
        settings.AUTH0_CLIENT_ID and
        settings.AUTH0_CLIENT_SECRET and
        settings.AUTH0_DOMAIN and
        settings.AUTH0_CALLBACK_URL
    )
