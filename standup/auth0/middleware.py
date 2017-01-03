from datetime import datetime, timedelta
from urllib.parse import urlparse

import requests
from requests.exceptions import ConnectTimeout, ReadTimeout
import simplejson

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from standup.auth0.models import IdToken


class Auth0LookupError(Exception):
    pass


def renew_id_token(id_token):
    """Renews id token and returns id token or None

    :arg str id_token: the id token to renew

    :returns: ``id_token`` or ``None``

    """
    url = 'https://{}/delegation'.format(settings.AUTH0_DOMAIN)
    response = requests.post(url, json={
        'client_id': settings.AUTH0_CLIENT_ID,
        'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
        'id_token': id_token,
        'api_type': 'app',
    }, timeout=settings.AUTH0_PATIENCE_TIMEOUT)

    try:
        result = response.json()
    except simplejson.JSONDecodeError:
        # This can happen if the response was someting like a 502 error
        return

    # If the response.status_code is not 200, it's still JSON but it won't have a id_token.
    return result.get('id_token')


def get_path(url):
    """Takes a url and returns path + querystring"""
    parsed = urlparse(url)
    if parsed.query:
        return '%s?%s' % (parsed.path, parsed.query)
    return parsed.path


class ValidateIDToken(object):
    """For users authenticated with an id_token, we need to check that it's still valid. For example,
    the user could have been blocked (e.g. leaving the company) if so we need to ask the user to log
    in again.

    """

    exception_paths = (
        get_path(settings.AUTH0_CALLBACK),
    )

    def process_request(self, request):
        if (
            request.method != 'POST' and
            not request.is_ajax() and
            request.user.is_active and
            request.path not in self.exception_paths
        ):
            # Look up expiration in session and see if the id_token needs to be renewed.
            id_token_expiration = request.session.get('id_token_expiration', None)
            if id_token_expiration and id_token_expiration < datetime.utcnow():
                return

            # Either no expiration in session or token needs to be renewed, so renew it
            # now.
            try:
                token = IdToken.objects.get(user=request.user)
            except IdToken.DoesNotExist:
                # If there is no IdToken, then this isn't a mozilla.com address and we're fine.
                return

            if token.id_token:
                try:
                    id_token = renew_id_token(token.id_token)
                except (ConnectTimeout, ReadTimeout):
                    messages.error(
                        request,
                        'Unable to validate your authentication with Auth0. '
                        'This can happen when there is temporary network '
                        'problem. Please sign in again.'
                    )
                    # Log the user out because their id_token didn't renew and send them to
                    # home page.
                    logout(request)
                    return HttpResponseRedirect(reverse(settings.AUTH0_SIGNIN_VIEW))

                if id_token:
                    # Save new token.
                    token.id_token = id_token
                    token.save()

                    # Re-up the session.
                    request.session['id_token_expiration'] = (
                        datetime.utcnow() + timedelta(seconds=settings.AUTH0_RENEW_ID_TOKEN_EXPIRY_SECONDS)
                    )

                else:
                    # If we don't have a new id_token, then it's not valid anymore. We log the user
                    # out and send them to the home page.
                    logout(request)
                    messages.error(
                        request,
                        'Unable to validate your authentication with Auth0. '
                        'This is most likely due to an expired authentication '
                        'session. You have to sign in again.'
                    )
                    return HttpResponseRedirect(reverse(settings.AUTH0_SIGNIN_VIEW))
