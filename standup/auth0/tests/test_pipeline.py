from django.http import HttpResponseRedirect

from standup.auth0 import pipeline
from standup.auth0.models import IdToken


class TestRunPipeline:
    def test_run_pipeline(self, db, django_user_model, request_factory):
        email_address = 'foo@example.com'
        user = django_user_model.objects.create_user(
            username=pipeline.email_to_username(email_address),
            password='foo',
            email=email_address
        )

        pl = [
            'standup.auth0.pipeline.get_user_by_username',
            'standup.auth0.pipeline.create_user',
            'standup.auth0.pipeline.reject_inactive_user'
        ]
        kwargs = {
            'user_info': {
                'nickname': 'foo',
                'email': email_address,
            },
            'request': request_factory.get('/')
        }
        ret = pipeline.run_pipeline(pl, **kwargs)
        assert ret['is_new'] is False
        assert ret['user'].id == user.id


class TestGetUserByUsername:
    def test_user_exists(self, db, django_user_model):
        email_address = 'foo@example.com'
        user = django_user_model.objects.create_user(
            username=pipeline.email_to_username(email_address),
            password='foo',
            email=email_address,
        )

        ret = pipeline.get_user_by_username(
            user_info={
                'nickname': 'foo',
                'email': email_address,
            },
            junk=123
        )
        assert ret['user'].id == user.id
        assert ret['is_new'] is False

        ret = pipeline.get_user_by_username(
            user_info={
                'nickname': 'FOO',
                'email': email_address.upper(),
            },
            junk=123
        )
        assert ret['user'].id == user.id
        assert ret['is_new'] is False

    def test_user_doesnt_exist(self, db):
        ret = pipeline.get_user_by_username(
            user_info={
                'nickname': 'foo',
                'email': 'rob@example.com',
            },
            junk=123
        )
        assert ret['is_new'] is True


class TestGetUserByEmail:
    def test_user_exists(self, db, django_user_model):
        user = django_user_model.objects.create_user(
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

    def test_user_doesnt_exist(self, db):
        ret = pipeline.get_user_by_email(
            user_info={'email': 'foo@example.com'},
            junk=123
        )
        assert ret['is_new'] is True


class TestCreateUser:
    def test_create_user_is_new(self, db):
        email_address = 'foo@example.com'
        ret = pipeline.create_user(
            user_info={
                'nickname': 'foo',
                'email': email_address
            },
            is_new=True,
            junk=123
        )
        # The system we use for generating usernames is stable and will always return the same
        # result.
        assert ret['user'].username == 'dn506rcIHEHguDYwURE50TAklmY'
        assert ret['user'].email == email_address

    def test_create_user_not_is_new(self, db):
        ret = pipeline.create_user(
            user_info={'nickname': 'foo', 'email': 'foo@example.com'},
            is_new=False,
            junk=123
        )
        assert ret is None


class TestRejectInactiveUser:
    def test_inactive(self, db, django_user_model, request_factory):
        user = django_user_model.objects.create_user(
            username='foo',
            password='foo',
            email='foo@example.com'
        )
        user.is_active = False
        user.save()

        request = request_factory.get('/')

        ret = pipeline.reject_inactive_user(
            request=request,
            user=user,
            is_new=False,
            junk=123
        )
        assert isinstance(ret, HttpResponseRedirect)

    def test_active(self, db, django_user_model, request_factory):
        user = django_user_model.objects.create_user(
            username='foo',
            password='foo',
            email='foo@example.com'
        )

        request = request_factory.get('/')

        ret = pipeline.reject_inactive_user(
            request=request,
            user=user,
            is_new=False,
            junk=123
        )
        assert ret is None


class TestRejectUnverifiedEmail:
    def test_verified(self, db, request_factory):
        request = request_factory.get('/')
        ret = pipeline.reject_unverified_email(
            request=request,
            user_info={'email_verified': True, 'email': 'foo@example.com'},
            junk=123
        )
        assert ret is None

    def test_not_verified(self, db, request_factory):
        request = request_factory.get('/')
        ret = pipeline.reject_unverified_email(
            request=request,
            user_info={'email_verified': False, 'email': 'foo@example.com'},
            junk=123
        )
        assert isinstance(ret, HttpResponseRedirect)


class TestRequireIdToken:
    def test_not_required(self, db, django_user_model, request_factory, settings):
        settings.AUTH0_ID_TOKEN_DOMAINS = ['mozilla.com']

        user = django_user_model.objects.create_user(
            username='foo',
            password='foo',
            email='foo@example.com'
        )

        request = request_factory.get('/')

        ret = pipeline.require_id_token(
            request=request,
            user=user,
            user_info={'email': 'foo@example.com'},
            token_info={'id_token': 'foo'},
            junk=123
        )
        assert ret is None

    def test_required_but_no_id_token(self, db, django_user_model, request_factory, settings):
        settings.AUTH0_ID_TOKEN_DOMAINS = ['mozilla.com']

        user = django_user_model.objects.create_user(
            username='foo',
            password='foo',
            email='foo@mozilla.com'
        )

        request = request_factory.get('/')

        ret = pipeline.require_id_token(
            request=request,
            user=user,
            user_info={'email': 'foo@mozilla.com'},
            token_info={},
            junk=123
        )
        assert isinstance(ret, HttpResponseRedirect)

    def test_required_and_id_token(self, db, django_user_model, request_factory, settings):
        settings.AUTH0_ID_TOKEN_DOMAINS = ['mozilla.com']

        user = django_user_model.objects.create_user(
            username='foo',
            password='foo',
            email='foo@mozilla.com'
        )

        request = request_factory.get('/')

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
