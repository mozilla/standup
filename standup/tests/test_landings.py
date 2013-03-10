from nose.tools import eq_
from standup.tests import BaseTestCase


class LandingsViewsTestCase(BaseTestCase):
    def test_help_view(self):
        response = self.client.get('/help')
        eq_(response.status_code, 200)
