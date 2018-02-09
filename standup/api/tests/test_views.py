import json

from django.urls import reverse
from django.utils.encoding import force_bytes
from django.test import Client, TestCase

import pytest

from standup.api.tests.factories import SystemTokenFactory
from standup.status.models import (
    Project,
    Status,
    StandupUser,
)
from standup.status.tests.factories import (
    ProjectFactory,
    StatusFactory,
    StandupUserFactory,
)


def _content_generator():
    """Generator for Jonathan Coulton songs"""
    content = [
        'Baby Got Back',
        'Chiron Beta Prime',
        'Christmas with You Is the Best',
        'Code Monkey',
        'I Crush Everything',
        'I Say Arrr, You Say Woo...',
        'Re: Your Brains',
        'Redshirt',
        'Shop Vac',
        'Skullcrusher Mountain',
        'Stroller Town',
        'The Presidents',
        'Todd the T1000',
        'When I\'m 25 or 64',
    ]
    while True:
        for song_title in content:
            yield song_title


content_generator = _content_generator()


class JSONClient(Client):
    """Django client that provides a .json_post() method

    The ``.json_post()`` method makes it easier to test API endpoints because it deals with
    converting the payload and adding appropriate headers.

    """
    def post_json(self, path, payload, secure=False, **extra):
        payload = force_bytes(json.dumps(payload))
        return self.generic('POST', path, payload, content_type='application/json',
                            secure=secure, **extra)

    def delete_json(self, path, payload, secure=False, **extra):
        payload = force_bytes(json.dumps(payload))
        return self.generic('DELETE', path, payload, content_type='application/json',
                            secure=secure, **extra)


class APITestCase(TestCase):
    """Django TestCase that uses the JSONClient"""
    client_class = JSONClient


class TestAPIView(APITestCase):
    """Tests the APIView using the StatusPost view"""
    def test_get_fails(self):
        """Verify GET fails because it's not an allowed method"""
        resp = self.client.get(reverse('api.status-create'))
        assert resp.status_code == 405
        assert resp['content_type'] == 'application/json'
        assert resp.content == b'{"error": "Method not allowed"}'


class TestStatusPost(APITestCase):
    def test_post(self):
        """Test minimal post"""
        token = SystemTokenFactory.create()
        standupuser = StandupUserFactory.create()

        content = next(content_generator)
        resp = self.client.post_json(
            reverse('api.status-create'),
            payload={
                'api_key': token.token,
                'user': standupuser.irc_nick,
                'content': content
            }
        )
        assert resp.status_code == 200
        post = Status.objects.get(content=content)
        assert post.user.id == standupuser.id

    def test_post_with_new_project(self):
        """Test post with an new project"""
        token = SystemTokenFactory.create()
        standupuser = StandupUserFactory.create()

        content = next(content_generator)
        resp = self.client.post_json(
            reverse('api.status-create'),
            payload={
                'api_key': token.token,
                'user': standupuser.irc_nick,
                'project': 'jcoulton',
                'content': content
            }
        )
        assert resp.status_code == 200
        post = Status.objects.get(content=content)
        assert post.user.id == standupuser.id
        project = Project.objects.filter(slug='jcoulton').first()
        assert post.project.id == project.id

    def test_post_with_existing_project(self):
        """Test post with an existing project"""
        token = SystemTokenFactory.create()
        standupuser = StandupUserFactory.create()
        project = ProjectFactory.create()

        content = next(content_generator)
        resp = self.client.post_json(
            reverse('api.status-create'),
            payload={
                'api_key': token.token,
                'user': standupuser.irc_nick,
                'project': project.slug,
                'content': content
            }
        )
        assert resp.status_code == 200
        post = Status.objects.get(content=content)
        assert post.user.id == standupuser.id
        assert post.project.id == project.id

    def test_post_no_auth(self):
        """Verify POST with no auth fails"""
        content = next(content_generator)
        resp = self.client.post_json(
            reverse('api.status-create'),
            payload={
                'user': 'jcoulton',
                'content': content
            }
        )
        assert resp.status_code == 403
        assert resp.content == b'{"error": "No api_key provided."}'

    def test_post_wrong_auth(self):
        """Verify POST fails with wrong auth token"""
        content = next(content_generator)
        resp = self.client.post_json(
            reverse('api.status-create'),
            payload={
                'api_key': 'ou812',
                'user': 'jcoulton',
                'content': content
            }
        )
        assert resp.status_code == 403
        assert resp.content == b'{"error": "Api key forbidden."}'


class TestStatusDelete(APITestCase):
    def test_delete(self):
        token = SystemTokenFactory.create()
        standupuser = StandupUserFactory.create()
        status = StatusFactory.create(user=standupuser)

        resp = self.client.delete_json(
            reverse('api.status-delete', kwargs={'pk': str(status.id)}),
            payload={
                'api_key': token.token,
                'user': standupuser.irc_nick,
            }
        )
        assert resp.status_code == 200
        assert resp.content == ('{"id": %s}' % (status.id,)).encode('utf-8')

    def test_invalid_username(self):
        token = SystemTokenFactory.create()
        standupuser = StandupUserFactory.create()
        status = StatusFactory.create(user=standupuser)

        resp = self.client.delete_json(
            reverse('api.status-delete', kwargs={'pk': str(status.id)}),
            payload={
                'api_key': token.token,
                'user': ''
            }
        )
        assert resp.status_code == 400
        assert resp.content == b'{"error": "Missing required fields."}'

    def test_status_does_not_exist(self):
        token = SystemTokenFactory.create()
        standupuser = StandupUserFactory.create()

        resp = self.client.delete_json(
            reverse('api.status-delete', kwargs={'pk': str(1000)}),
            payload={
                'api_key': token.token,
                'user': standupuser.irc_nick,
            }
        )
        assert resp.status_code == 400
        assert resp.content == b'{"error": "Status does not exist."}'

    def test_wrong_user(self):
        token = SystemTokenFactory.create()
        standupuser = StandupUserFactory.create(user__username='charlie')
        status = StatusFactory.create(user=standupuser)

        resp = self.client.delete_json(
            reverse('api.status-delete', kwargs={'pk': str(status.id)}),
            payload={
                'api_key': token.token,
                'user': 'fred',
            }
        )
        assert resp.status_code == 403
        assert resp.content == b'{"error": "You cannot delete this status."}'


@pytest.mark.xfail(reason='Update is disabled until we reimplement it')
class TestUpdateUser(APITestCase):
    def test_update_name(self):
        token = SystemTokenFactory.create()
        standupuser = StandupUserFactory.create(name='Data')

        resp = self.client.post_json(
            reverse('api.user-update', kwargs={'username': standupuser.irc_nick}),
            payload={
                'api_key': token.token,
                'name': 'Lor',
            }
        )
        assert resp.status_code == 200
        standupuser = StandupUser.objects.get(pk=standupuser.id)
        assert standupuser.name == 'Lor'

    def test_update_email(self):
        token = SystemTokenFactory.create()
        standupuser = StandupUserFactory.create(email='data@example.com')

        resp = self.client.post_json(
            reverse('api.user-update', kwargs={'username': standupuser.irc_nick}),
            payload={
                'api_key': token.token,
                'email': 'lor@example.com',
            }
        )
        assert resp.status_code == 200
        standupuser = StandupUser.objects.get(pk=standupuser.id)
        assert standupuser.email == 'lor@example.com'

    def test_user_does_not_exist(self):
        token = SystemTokenFactory.create()

        resp = self.client.post_json(
            reverse('api.user-update', kwargs={'username': 'cmdrdata'}),
            payload={
                'api_key': token.token,
                'name': 'lor',
            }
        )
        assert resp.status_code == 400
        assert resp.content == b'{"error": "User does not exist."}'
