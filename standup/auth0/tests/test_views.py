from django.core.urlresolvers import reverse

import requests_mock

from standup.auth0.settings import app_settings


def is_redirect_to(resp, expected_url):
    return (
        resp.status_code == 302 and
        resp['Location'] == expected_url
    )


SIGNIN_VIEW = 'http://testserver' + reverse(app_settings.AUTH0_SIGNIN_VIEW)


class TestAuth0LoginCallback:
    def test_no_state(self, db, client, messages_catcher):
        with requests_mock.Mocker():
            resp = client.get(app_settings.AUTH0_CALLBACK_URL)

            assert is_redirect_to(resp, SIGNIN_VIEW)
            assert messages_catcher.get_messages() == []

    def test_bad_state(self, db, client, messages_catcher):
        with requests_mock.Mocker():
            client.session['state'] = 'bah'
            resp = client.get(app_settings.AUTH0_CALLBACK_URL + '?state=whatever&code=ou812')

            assert is_redirect_to(resp, SIGNIN_VIEW)
            assert messages_catcher.get_messages() == []

    def test_no_code(self, db, client, messages_catcher):
        with requests_mock.Mocker():
            client.session['state'] = 'whatever'
            resp = client.get(app_settings.AUTH0_CALLBACK_URL + '?state=whatever')

            assert is_redirect_to(resp, SIGNIN_VIEW)
            assert messages_catcher.get_messages() == []

    def test_no_code_with_error(self, db, client, messages_catcher):
        with requests_mock.Mocker():
            session = client.session
            session['auth0_state'] = 'whatever'
            session.save()
            resp = client.get(app_settings.AUTH0_CALLBACK_URL + '?state=whatever&error=foo')

            assert is_redirect_to(resp, SIGNIN_VIEW)
            assert (
                messages_catcher.get_messages()[0]['message'] ==
                'Unable to sign in because of an error from Auth0. (foo)'
            )

    def test_no_access_token(self, db, client, messages_catcher):
        with requests_mock.Mocker() as req_mock:
            req_mock.register_uri(
                'POST', 'https://%s/oauth/token' % app_settings.AUTH0_DOMAIN,
                json={}
            )
            session = client.session
            session['auth0_state'] = 'whatever'
            session.save()

            resp = client.get(app_settings.AUTH0_CALLBACK_URL + '?state=whatever&code=123')

            assert is_redirect_to(resp, SIGNIN_VIEW)
            assert (
                messages_catcher.get_messages()[0]['message'] ==
                'Unable to authenticate with Auth0 at this time. Please refresh to try again.'
            )

    def test_success(self, settings, db, client, messages_catcher):
        settings.AUTH0_PIPELINE = []

        with requests_mock.Mocker() as req_mock:
            req_mock.register_uri(
                'POST', 'https://%s/oauth/token' % app_settings.AUTH0_DOMAIN,
                json={'access_token': 'accessgranted'}
            )

            req_mock.register_uri(
                'GET', 'https://%s/userinfo?access_token=accessgranted' % app_settings.AUTH0_DOMAIN,
                json={'id_token': 'ou812'}
            )

            session = client.session
            session['auth0_state'] = 'whatever'
            session.save()

            resp = client.get(app_settings.AUTH0_CALLBACK_URL + '?state=whatever&code=123')

            # Verify token_info request
            assert (
                req_mock.request_history[0].url ==
                'https://%s/oauth/token' % app_settings.AUTH0_DOMAIN
            )
            assert (
                req_mock.request_history[0].json() ==
                {
                    'client_id': app_settings.AUTH0_CLIENT_ID,
                    'client_secret': app_settings.AUTH0_CLIENT_SECRET,
                    'redirect_uri': app_settings.AUTH0_CALLBACK_URL,
                    'code': '123',
                    'grant_type': 'authorization_code'
                }
            )

            # Verify user_info request
            assert (
                req_mock.request_history[1].url ==
                'https://%s/userinfo?access_token=accessgranted' % app_settings.AUTH0_DOMAIN
            )

            # Assert we get redirected to the front page
            assert is_redirect_to(resp, 'http://testserver/')
