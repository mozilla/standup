from django.test import TransactionTestCase

from standup.auth0 import utils


class UtilitiesTestCase(TransactionTestCase):
    def test_get_or_create_user_new_user(self):
        user = utils.get_or_create_user('test@example.com')
        assert user.email == 'test@example.com'
        assert user.username == 'test'
        assert user.profile.name is None

    def test_get_or_create_user_same_user(self):
        user = utils.get_or_create_user('test@example.com')
        user2 = utils.get_or_create_user('test@example.com')
        assert user.id == user2.id

    def test_get_or_create_user_username_generation(self):
        utils.get_or_create_user('test@example.com', name='test')
        user2 = utils.get_or_create_user('foo@example.com', name='test')
        assert user2.email == 'foo@example.com'
        assert user2.username == 'test2'

    def test_get_or_create_profile_new_user(self):
        user = utils.get_or_create_user('test@example.com')
        profile = utils.get_or_create_profile(user)
        assert profile.slug == user.username

    def test_get_or_create_profile_existing_user(self):
        user = utils.get_or_create_user('test@example.com')
        profile = utils.get_or_create_profile(user)
        assert profile.slug == user.username

        profile.slug = 'ou812'
        profile.save()
        profile = utils.get_or_create_profile(user)
        assert profile.slug == 'ou812'

    def test_get_or_create_profile_slug_generation(self):
        user = utils.get_or_create_user('test@example.com')
        profile = utils.get_or_create_profile(user)
        profile.slug = 'foo'
        profile.save()

        user2 = utils.get_or_create_user('foo@example.com')
        profile2 = utils.get_or_create_profile(user2)

        assert profile2.slug == 'foo2'
