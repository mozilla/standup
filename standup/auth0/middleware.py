from datetime import datetime, timedelta
from urllib.parse import urlparse

import requests
from requests.exceptions import ConnectTimeout, ReadTimeout
import simplejson

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from standup.auth0.models import IdToken


class Auth0LookupError(Exception):
    pass


def renew_id_token(id_token):
    """Renews id token and returns delegation result or None

    :arg str id_token: the id token to renew

    :returns: delegation result (dict) ``None``

    """
    url = 'https://%s/delegation' % settings.AUTH0_DOMAIN
    response = requests.post(url, json={
        'client_id': settings.AUTH0_CLIENT_ID,
        'api_type': 'app',
        'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
        'id_token': id_token,
    }, timeout=settings.AUTH0_PATIENCE_TIMEOUT)

    try:
        result = response.json()
    except simplejson.JSONDecodeError:
        # This can happen if the response was someting like a 502 error
        return

    # If the response.status_code is not 200, it's still JSON but it won't have a id_token.
    return result.get('id_token')


class ValidateIdToken(object):
    """For users authenticated with an id_token, we need to check that it's still valid. For
    example, the user could have been blocked (e.g. leaving the company) if so we need to ask the
    user to log in again.

    We do this using cache.

    # FIXME(willkg): Rework this so that the cache parts are methods that can be overridden.

    """

    exception_paths = (
        # Exclude the AUTH0_CALLBACK_URL path, otherwise this can loop
        urlparse(settings.AUTH0_CALLBACK_URL).path,
    )

    def process_request(self, request):
        if (
                request.method != 'POST' and
                # FIXME(willkg): We might want to do this for AJAX, too, otherwise one-page webapps
                # might never renew.
                not request.is_ajax() and
                request.user.is_active and
                request.user.email and
                request.path not in self.exception_paths
        ):
            # Verify their domain is one of the domains we need to look at
            domain = request.user.email.lower().split('@', 1)[1]
            if domain not in settings.AUTH0_ID_TOKEN_DOMAINS:
                return

            cache_key = 'auth0:renew_id_token:%s' % request.user.id

            # Look up expiration in cache to see if id_token needs to be renewed
            # FIXME(willkg): Try named cache and if that doesn't exist, fall back to default.
            if cache.get(cache_key):
                return

            # The id_token has expired, so we renew it now
            try:
                token = IdToken.objects.get(user=request.user)

            except IdToken.DoesNotExist:
                # If there is no IdToken then something is weird because they should have one. So
                # log them out and tell them to sign in
                messages.error(
                    request,
                    'You can\'t log in with that email address using the provider you '
                    'used. Please log in with the Oauth2 provider.',
                    fail_silently=True
                )
                logout(request.user)
                return HttpResponseRedirect(reverse(settings.AUTH0_SIGNIN_VIEW))

            try:
                new_id_token = renew_id_token(token.id_token)

            except (ConnectTimeout, ReadTimeout):
                # Log the user out because their id_token didn't renew and send them to
                # home page
                messages.error(
                    request,
                    'Unable to validate your authentication with Auth0. '
                    'This can happen when there is temporary network '
                    'problem. Please sign in again.',
                    fail_silently=True
                )
                logout(request)
                return HttpResponseRedirect(reverse(settings.AUTH0_SIGNIN_VIEW))

            if new_id_token:
                # Save new token and re-up it in cache--all set!
                token.id_token = new_id_token
                token.expire = datetime.utcnow() + timedelta(seconds=settings.AUTH0_ID_TOKEN_EXPIRY)
                token.save()

                cache.set(cache_key, True, settings.AUTH0_ID_TOKEN_EXPIRY)
                return

            # If we don't have a new id_token, then it's not valid anymore. We log the user
            # out and send them to the home page
            messages.error(
                request,
                'Unable to validate your authentication with Auth0. '
                'This is most likely due to an expired authentication '
                'session. You have to sign in again.',
                fail_silently=True
            )
            logout(request)
            return HttpResponseRedirect(reverse(settings.AUTH0_SIGNIN_VIEW))
