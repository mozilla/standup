from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect
from django.test import TestCase
from django.test.client import RequestFactory

from standup.auth0 import pipeline
from standup.auth0.models import IdToken


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

        ret = pipeline.get_user_by_username(
            user_info={'nickname': 'foo'},
            junk=123
        )
        assert ret['user'].id == user.id
        assert ret['is_new'] is False

        ret = pipeline.get_user_by_username(
            user_info={'nickname': 'FOO'},
            junk=123
        )
        assert ret['user'].id == user.id
        assert ret['is_new'] is False

    def test_user_doesnt_exist(self):
        ret = pipeline.get_user_by_username(
            user_info={'nickname': 'foo'},
            junk=123
        )
        assert ret['is_new'] is True


class GetUserByEmailTestCase(TestCase):
    def test_user_exists(self):
        User = get_user_model()
        user = User.objects.create_user(
            username='foo',
            password='foo',
            email='foo@example.com'
        )

        ret = pipeline.get_user_by_email(
            user_info={'email': 'foo@example.com'},
            junk=123
        )
        assert ret['user'].id == user.id
        assert ret['is_new'] is False

        ret = pipeline.get_user_by_email(
            user_info={'email': 'FOO@example.com'},
            junk=123
        )
        assert ret['user'].id == user.id
        assert ret['is_new'] is False

    def test_user_doesnt_exist(self):
        ret = pipeline.get_user_by_email(
            user_info={'email': 'foo@example.com'},
            junk=123
        )
        assert ret['is_new'] is True


class CreateUserTestCase(TestCase):
    def test_create_user_is_new(self):
        ret = pipeline.create_user(
            user_info={'nickname': 'foo', 'email': 'foo@example.com'},
            is_new=True,
            junk=123
        )
        assert ret['user'].username == 'foo'
        assert ret['user'].email == 'foo@example.com'

    def test_create_user_not_is_new(self):
        ret = pipeline.create_user(
            user_info={'nickname': 'foo', 'email': 'foo@example.com'},
            is_new=False,
            junk=123
        )
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

        ret = pipeline.reject_inactive_user(
            request=request,
            user=user,
            is_new=False,
            junk=123
        )
        assert isinstance(ret, HttpResponseRedirect)

    def test_active(self):
        User = get_user_model()
        user = User.objects.create_user(
            username='foo',
            password='foo',
            email='foo@example.com'
        )

        request = self.factory.get('/')

        ret = pipeline.reject_inactive_user(
            request=request,
            user=user,
            is_new=False,
            junk=123
        )
        assert ret is None


class RejectUnverifiedEmailTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_verified(self):
        request = self.factory.get('/')
        ret = pipeline.reject_unverified_email(
            request=request,
            user_info={'email_verified': True, 'email': 'foo@example.com'},
            junk=123
        )
        assert ret is None

    def test_not_verified(self):
        request = self.factory.get('/')
        ret = pipeline.reject_unverified_email(
            request=request,
            user_info={'email_verified': False, 'email': 'foo@example.com'},
            junk=123
        )
        assert isinstance(ret, HttpResponseRedirect)


# FIXME(willkg): RequireIdTokenTestCase
class RequireIdTokenTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_not_required(self):
        User = get_user_model()
        user = User.objects.create_user(
            username='foo',
            password='foo',
            email='foo@example.com'
        )

        request = self.factory.get('/')

        with self.settings(AUTH0_ID_TOKEN_DOMAINS=['mozilla.com']):
            ret = pipeline.require_id_token(
                request=request,
                user=user,
                user_info={'email': 'foo@example.com'},
                token_info={'id_token': 'foo'},
                junk=123
            )
            assert ret is None

    def test_required_but_no_id_token(self):
        User = get_user_model()
        user = User.objects.create_user(
            username='foo',
            password='foo',
            email='foo@mozilla.com'
        )

        request = self.factory.get('/')

        with self.settings(AUTH0_ID_TOKEN_DOMAINS=['mozilla.com']):
            ret = pipeline.require_id_token(
                request=request,
                user=user,
                user_info={'email': 'foo@mozilla.com'},
                token_info={},
                junk=123
            )
            assert isinstance(ret, HttpResponseRedirect)

    def test_required_and_id_token(self):
        User = get_user_model()
        user = User.objects.create_user(
            username='foo',
            password='foo',
            email='foo@mozilla.com'
        )

        request = self.factory.get('/')

        with self.settings(AUTH0_ID_TOKEN_DOMAINS=['mozilla.com']):
            ret = pipeline.require_id_token(
                request=request,
                user=user,
                user_info={'email': 'foo@mozilla.com'},
                token_info={'id_token': 'foo'},
                junk=123
            )
            assert ret is None
            assert IdToken.objects.get(user=user).id_token == 'foo'

# FIXME(willkg): LoginUserTestCase: This requires a session which we can't (easily) fake with a
# RequestFactory.
