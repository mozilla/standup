from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.views.generic import View

import requests
from requests.exceptions import ConnectTimeout, ReadTimeout

from standup.auth0.pipeline import run_pipeline


class Auth0LoginCallback(View):
    def get(self, request):
        """Auth0 redirects to this view so we can log the user in

        This handles creating User and StandupUser objects if needed.

        """
        # Verify that the STATE we sent in is the same; no match--send user back to the signin view
        if not request.session or request.session.get('auth0_state') != request.GET.get('state', ''):
            return HttpResponseRedirect(reverse(settings.AUTH0_SIGNIN_VIEW))

        # Get the code from the request so we can verify it
        code = request.GET.get('code', '')
        if not code:
            if request.GET.get('error'):
                messages.error(
                    request,
                    'Unable to sign in because of an error from Auth0. ({msg})'.format(
                        msg=request.GET.get('error_description', request.GET['error'])
                    ),
                    fail_silently=True
                )
                return HttpResponseRedirect(reverse(settings.AUTH0_SIGNIN_VIEW))

            else:
                # No code and no error--send the user back to the signin view
                return HttpResponseRedirect(reverse(settings.AUTH0_SIGNIN_VIEW))

        # Verify the code
        json_header = {
            'content-type': 'application/json'
        }

        # https://tools.ietf.org/html/rfc6749#section-5.1
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

            # FIXME(willkg): Improve this to more correctly handle the various
            # oauth2 token situations.
            # https://tools.ietf.org/html/rfc6749#section-5.2
            if not token_info.get('access_token'):
                messages.error(
                    request,
                    'Unable to authenticate with Auth0 at this time. Please refresh to '
                    'try again.'
                )
                return HttpResponseRedirect(reverse(settings.AUTH0_SIGNIN_VIEW))

            user_url = 'https://{domain}/userinfo?{querystring}'.format(
                domain=settings.AUTH0_DOMAIN,
                querystring=urlencode({'access_token': token_info['access_token']})
            )

            user_info = requests.get(user_url).json()

        except (ConnectTimeout, ReadTimeout):
            messages.error(
                request,
                'Unable to authenticate with Auth0 at this time. Please wait a bit '
                'and try again.'
            )
            return HttpResponseRedirect(reverse(settings.AUTH0_SIGNIN_VIEW))

        # We've got our user_info and all our auth0 stuff is done; run through the pipeline and
        # return whatever we get
        kwargs = {
            'request': request,
            'user_info': user_info,
            'token_info': token_info,
        }
        result = run_pipeline(settings.AUTH0_PIPELINE, **kwargs)
        if result and not isinstance(result, dict):
            # If we got a truthy but non-dict back, then it's probably a response and we should just
            # return that
            return result

        # This goes to /--if someone wants it to go somewhere else, they can do it as a pipeline
        # rule
        return HttpResponseRedirect('/')
