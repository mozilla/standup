from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.core.urlresolvers import reverse
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.views.generic import View

import requests
from requests.exceptions import ConnectTimeout, ReadTimeout

from standup.auth0.utils import get_or_create_profile, get_or_create_user


class Auth0LoginCallback(View):
    def get(self, request):
        """Auth0 redirects to this view so we can log the user in

        This handles creating User and StandupUser objects if needed.

        """
        code = request.GET.get('code', '')

        if not code:
            if request.GET.get('error'):
                messages.error(
                    request,
                    'Unable to sign in because of an error from Auth0. ({msg})'.format(
                        msg=request.GET.get('error_description', request.GET['error'])
                    )
                )
                return HttpResponseRedirect(reverse('users.loginform'))
            return HttpResponseBadRequest('Missing "code"')

        json_header = {
            'content-type': 'application/json'
        }

        token_url = 'https://{domain}/oauth/token'.format(domain=settings.AUTH0_DOMAIN)

        token_payload = {
            'client_id': settings.AUTH0_CLIENT_ID,
            'client_secret': settings.AUTH0_CLIENT_SECRET,
            'redirect_uri': settings.AUTH0_CALLBACK_URL,
            'code': code,
            'grant_type': 'authorization_code'
        }

        try:
            token_info = requests.post(
                token_url,
                headers=json_header,
                json=token_payload,
                timeout=settings.AUTH0_PATIENCE_TIMEOUT
            ).json()

            if not token_info.get('access_token'):
                messages.error(
                    request,
                    'Unable to authenticate with Auth0 at this time. Please refresh to '
                    'try again.'
                )
                return HttpResponseRedirect(reverse('users.loginform'))

            user_url = 'https://{domain}/userinfo?access_token={access_token}'.format(
                domain=settings.AUTH0_DOMAIN, access_token=token_info['access_token']
            )

            user_info = requests.get(user_url).json()

        except (ConnectTimeout, ReadTimeout):
            messages.error(
                request,
                'Unable to authenticate with Auth0 at this time. Please wait a bit '
                'and try again.'
            )
            return HttpResponseRedirect(reverse('users.loginform'))

        # Get or create User instance using email address and nickname
        user = get_or_create_user(user_info['email'], user_info.get('nickname'))

        # If inactive, add message and redirect to login page
        if not user.is_active:
            messages.error(
                request,
                'This user account is inactive.'
            )
            return HttpResponseRedirect(reverse('users.loginform'))

        # Make sure they have a profile
        get_or_create_profile(user)

        # Log the user in
        # FIXME(willkg): This is sort of a lie--should we have our own backend?
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)

        return HttpResponseRedirect(reverse('status.index'))
