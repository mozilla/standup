from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.client import RequestFactory

from standup.auth0 import pipeline


class RunPipelineTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_run_pipeline(self):
        User = get_user_model()
        user = User.objects.create_user(
            username='foo',
            password='foo',
            email='foo@example.com'
        )

        pl = [
            'standup.auth0.pipeline.get_user_by_username',
            'standup.auth0.pipeline.create_user',
            'standup.auth0.pipeline.reject_inactive_user'
        ]
        kwargs = {
            'user_info': {
                'nickname': 'foo',
            },
            'request': self.factory.get('/')
        }
        ret = pipeline.run_pipeline(pl, **kwargs)
        assert ret['is_new'] is False
        assert ret['user'].id == user.id


class GetUserByUsernameTestCase(TestCase):
    def test_user_exists(self):
        User = get_user_model()
        user = User.objects.create_user(
            username='foo',
            password='foo',
            email='foo@example.com'
        )

        ret = pipeline.get_user_by_username({'nickname': 'foo'})
        assert ret['user'].id == user.id
        assert ret['is_new'] is False

        ret = pipeline.get_user_by_username({'nickname': 'FOO'})
        assert ret['user'].id == user.id
        assert ret['is_new'] is False

    def test_user_doesnt_exist(self):
        ret = pipeline.get_user_by_username({'nickname': 'foo'})
        assert ret['is_new'] is True


class GetUserByEmailTestCase(TestCase):
    def test_user_exists(self):
        User = get_user_model()
        user = User.objects.create_user(
            username='foo',
            password='foo',
            email='foo@example.com'
        )

        ret = pipeline.get_user_by_email({'email': 'foo@example.com'})
        assert ret['user'].id == user.id
        assert ret['is_new'] is False

        ret = pipeline.get_user_by_email({'email': 'FOO@example.com'})
        assert ret['user'].id == user.id
        assert ret['is_new'] is False

    def test_user_doesnt_exist(self):
        ret = pipeline.get_user_by_email({'email': 'foo@example.com'})
        assert ret['is_new'] is True


class CreateUserTestCase(TestCase):
    def test_create_user_is_new(self):
        ret = pipeline.create_user({'nickname': 'foo', 'email': 'foo@example.com'}, is_new=True)
        assert ret['user'].username == 'foo'
        assert ret['user'].email == 'foo@example.com'

    def test_create_user_not_is_new(self):
        ret = pipeline.create_user({'nickname': 'foo', 'email': 'foo@example.com'}, is_new=False)
        assert ret is None


class RejectInactiveUserTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_inactive(self):
        User = get_user_model()
        user = User.objects.create_user(
            username='foo',
            password='foo',
            email='foo@example.com'
        )
        user.is_active = False
        user.save()

        request = self.factory.get('/')

        ret = pipeline.reject_inactive_user(request, user)
        assert ret is not None

    def test_active(self):
        User = get_user_model()
        user = User.objects.create_user(
            username='foo',
            password='foo',
            email='foo@example.com'
        )

        request = self.factory.get('/')

        ret = pipeline.reject_inactive_user(request, user)
        assert ret is None
