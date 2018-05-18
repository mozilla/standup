from django.core.urlresolvers import reverse
from django.test import TestCase


class StatisticsViewTestCase(TestCase):
    def test_unauthenticated_redirects(self):
        resp = self.client.get(reverse('manage.statistics'))
        assert resp.status_code == 302

    # FIXME(willkg): add test for authenticated and staff
