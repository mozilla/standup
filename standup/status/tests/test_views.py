from django.core.urlresolvers import reverse
from django.test import TestCase

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

    def test_status_404(self):
        resp = self.client.get(reverse('status.status', kwargs={'pk': 1234}))
        assert resp.status_code == 404
