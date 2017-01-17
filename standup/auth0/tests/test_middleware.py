from datetime import datetime, timedelta
from urllib.parse import urlparse

from django import http
from django.contrib.auth.models import AnonymousUser
from django.core.urlresolvers import reverse

from requests.exceptions import ReadTimeout
import requests_mock

from standup.auth0.middleware import ValidateIdToken
from standup.auth0.models import IdToken


class TestMiddleware:
    def test_renew_successfully(self, settings, db, django_user_model, request_factory):
        auth0_domain = 'auth0.example.com'

        settings.AUTH0_DOMAIN = auth0_domain
        settings.AUTH0_ID_TOKEN_DOMAINS = ['example.com']

        user = django_user_model.objects.create(email='test@example.com')
        id_token = IdToken.objects.create(
            user=user,
            id_token='12345.6789.01234',
            expire=datetime.utcnow() + timedelta(seconds=900)
        )
        request = request_factory.get('/')
        request.user = user

        with requests_mock.Mocker() as req_mock:
            # First time, this is hit, it returns "new_token"
            req_mock.register_uri(
                'POST', 'https://%s/delegation' % auth0_domain,
                json={'id_token': 'new_token'}
            )

            # Run the middleware and assert it didn't return an HTTP redirect
            middleware = ValidateIdToken()
            result = middleware.process_request(request)
            assert result is None

            # Verify the id_token changed
            user_profile = IdToken.objects.get(id=id_token.id)
            assert user_profile.id_token == 'new_token'

        with requests_mock.Mocker() as req_mock:
            # Now it returns "new_token_2"
            req_mock.register_uri(
                'POST', 'https://%s/delegation' % auth0_domain,
                json={'id_token': 'new_token_2'}
            )

            # Run the middleware again; this time the token hasn't expired, so it shouldn't run
            # through the renew code
            result = middleware.process_request(request)
            assert result is None

            # Verify the id_token did not change
            user_profile = IdToken.objects.get(id=id_token.id)
            assert user_profile.id_token == 'new_token'

    def test_renewal_failure_logs_you_out(self, settings, db, django_user_model, request_factory):
        auth0_domain = 'auth0.example.com'

        settings.AUTH0_DOMAIN = auth0_domain
        settings.AUTH0_ID_TOKEN_DOMAINS = ['example.com']

        user = django_user_model.objects.create(email='test@example.com')
        IdToken.objects.create(
            user=user,
            id_token='12345.6789.01234',
            expire=datetime.utcnow() + timedelta(seconds=900)
        )
        request = request_factory.get('/')
        request.user = user

        with requests_mock.Mocker() as req_mock:
            # No id_token, so renewal is a failure
            req_mock.register_uri(
                'POST', 'https://%s/delegation' % auth0_domain,
                json={}
            )

            middleware = ValidateIdToken()
            result = middleware.process_request(request)

            # Redirected to the sign in page
            assert isinstance(result, http.HttpResponseRedirect)
            assert result.url == reverse(settings.AUTH0_SIGNIN_VIEW)

    def test_ignore_post_requests(self, db, django_user_model, request_factory):
        user = django_user_model.objects.create(email='test@example.com')
        IdToken.objects.create(
            user=user,
            id_token='12345.6789.01234',
            expire=datetime.utcnow() + timedelta(seconds=900)
        )

        middleware = ValidateIdToken()

        # All requests will throw an error
        with requests_mock.Mocker():
            request = request_factory.post('/')
            request.user = user
            result = middleware.process_request(request)
            assert result is None

    def test_ignore_ajax_requests(self, db, django_user_model, request_factory):
        user = django_user_model.objects.create(email='test@example.com')
        IdToken.objects.create(
            user=user,
            id_token='12345.6789.01234',
            expire=datetime.utcnow() + timedelta(seconds=900)
        )

        middleware = ValidateIdToken()

        # All requests will throw an error
        with requests_mock.Mocker():
            request = request_factory.get('/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            request.user = user
            result = middleware.process_request(request)
            assert result is None

    def test_ignore_inactive_users(self, db, django_user_model, request_factory):
        user = django_user_model.objects.create(email='test@example.com')
        IdToken.objects.create(
            user=user,
            id_token='12345.6789.01234',
            expire=datetime.utcnow() + timedelta(seconds=900)
        )

        middleware = ValidateIdToken()

        # All requests will throw an error
        with requests_mock.Mocker():
            user.is_active = False
            request = request_factory.get('/')
            request.user = user
            result = middleware.process_request(request)
            assert result is None

    def test_ignore_anonymous_users(self, db, request_factory):
        middleware = ValidateIdToken()

        with requests_mock.Mocker():
            request = request_factory.get('/')
            request.user = AnonymousUser()
            result = middleware.process_request(request)
            assert result is None

    def test_ignore_auth0_callback_url(self, settings, db, django_user_model, request_factory):
        user = django_user_model.objects.create(email='test@example.com')
        IdToken.objects.create(
            user=user,
            id_token='12345.6789.01234',
            expire=datetime.utcnow() + timedelta(seconds=900)
        )

        middleware = ValidateIdToken()

        # All requests will throw an error
        with requests_mock.Mocker():
            user.is_active = True
            request = request_factory.get(urlparse(settings.AUTH0_CALLBACK_URL).path)
            request.user = user
            result = middleware.process_request(request)
            assert result is None

    def test_renewal_timed_out(self, settings, db, django_user_model, request_factory):
        auth0_domain = 'auth0.example.com'

        settings.AUTH0_DOMAIN = auth0_domain
        settings.AUTH0_ID_TOKEN_DOMAINS = ['example.com']

        user = django_user_model.objects.create(email='test@example.com')
        IdToken.objects.create(
            user=user,
            id_token='12345.6789.01234',
            expire=datetime.utcnow() + timedelta(seconds=900)
        )

        def json_callback(*args, **kwargs):
            raise ReadTimeout('too long')

        with requests_mock.Mocker() as req_mock:
            req_mock.register_uri(
                'POST', 'https://%s/delegation' % auth0_domain,
                json=json_callback
            )

            request = request_factory.get('/')
            request.user = user
            middleware = ValidateIdToken()
            result = middleware.process_request(request)

            # Redirected to the sign in page
            assert isinstance(result, http.HttpResponseRedirect)
            assert result.url == reverse(settings.AUTH0_SIGNIN_VIEW)
