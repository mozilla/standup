from django.urls import reverse
from django.test import override_settings, TestCase

from standup.status.tests.factories import StatusFactory


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
