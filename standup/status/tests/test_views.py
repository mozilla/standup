from django.core.urlresolvers import reverse
from django.test import override_settings, TestCase, TransactionTestCase

from standup.status.tests.factories import StatusFactory
from standup.status import views


class UtilitiesTestCase(TransactionTestCase):
    def test_get_or_create_user_new_user(self):
        user = views.get_or_create_user('test@example.com')
        assert user.email == 'test@example.com'
        assert user.username == 'test'
        assert user.profile.name is None

    def test_get_or_create_user_same_user(self):
        user = views.get_or_create_user('test@example.com')
        user2 = views.get_or_create_user('test@example.com')
        assert user.id == user2.id

    def test_get_or_create_user_username_generation(self):
        views.get_or_create_user('test@example.com', name='test')
        user2 = views.get_or_create_user('foo@example.com', name='test')
        assert user2.email == 'foo@example.com'
        assert user2.username == 'test2'

    def test_get_or_create_profile_new_user(self):
        user = views.get_or_create_user('test@example.com')
        profile = views.get_or_create_profile(user)
        assert profile.slug == user.username

    def test_get_or_create_profile_existing_user(self):
        user = views.get_or_create_user('test@example.com')
        profile = views.get_or_create_profile(user)
        assert profile.slug == user.username

        profile.slug = 'ou812'
        profile.save()
        profile = views.get_or_create_profile(user)
        assert profile.slug == 'ou812'

    def test_get_or_create_profile_slug_generation(self):
        user = views.get_or_create_user('test@example.com')
        profile = views.get_or_create_profile(user)
        profile.slug = 'foo'
        profile.save()

        user2 = views.get_or_create_user('foo@example.com')
        profile2 = views.get_or_create_profile(user2)

        assert profile2.slug == 'foo2'


class HomeViewTestCase(TestCase):
    def test_empty(self):
        resp = self.client.get(reverse('status.index'))
        assert resp.status_code == 200
        self.assertContains(resp, 'No status updates available')

    def test_single_page(self):
        # The page length is 20, so we build just 5
        StatusFactory.create_batch(5)
        resp = self.client.get(reverse('status.index'))
        assert resp.status_code == 200
        # FIXME: Need a better assertion here. Should probably assert that 5
        # statuses got rendered.
        self.assertNotContains(resp, 'No status updates available')


class StatusViewTestCase(TestCase):
    def test_status_404(self):
        resp = self.client.get(reverse('status.status', kwargs={'pk': 1234}))
        assert resp.status_code == 404


class RobotsViewTestCase(TestCase):
    @override_settings(ROBOTS_ALLOW=True)
    def test_robots_allow(self):
        # response should be empty for allow
        resp = self.client.get('/robots.txt')
        assert resp.status_code == 200
        assert resp['content-type'] == 'text/plain'
        assert not resp.content

    @override_settings(ROBOTS_ALLOW=False)
    def test_robots_disallow(self):
        # response should be the disallow all string
        resp = self.client.get('/robots.txt')
        assert resp.status_code == 200
        assert resp['content-type'] == 'text/plain'
        assert resp.content == b'User-agent: *\nDisallow: /'


class StatisticsViewTestCase(TestCase):
    def test_statistics(self):
        resp = self.client.get(reverse('status.statistics'))
        assert resp.status_code == 200
