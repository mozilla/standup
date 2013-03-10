import unittest

import simplejson as json
from flask import render_template_string
from nose.tools import eq_
from standup.apps.api2.decorators import api_key_required
from standup.apps.api2.helpers import numerify
from standup.tests import BaseTestCase, project, status, user


class HelpersTestCase(unittest.TestCase):
    def test_numerify(self):
        """Test the `numerify` helper function"""
        # Test numeric string
        eq_(numerify('1'), 1)

        # Test invalid type with default
        eq_(numerify(None, 1), 1)

        # Test invalid value with default
        eq_(numerify('', 1), 1)

        # Test below limit
        eq_(numerify('25', lower=50), 50)

        # Test within limit
        eq_(numerify('50', lower=25, upper=75), 50)

        # Test upper limit
        eq_(numerify('75', upper=50), 50)

        # Throws a type error when a invalid type is provided with no default
        try:
            numerify(None)
        except TypeError:
            assert True

        # Throws a value error when an invalid value is provided with no
        # default
        try:
            numerify('a')
        except ValueError:
            assert True


class DecoratorsTestCase(BaseTestCase):
    def __init__(self, *args, **kwargs):
        super(DecoratorsTestCase, self).__init__(*args, **kwargs)

        @self.app.route('/_tests/_api/_protected', methods=['POST'])
        @api_key_required
        def protected():
            return render_template_string('Success!')

    def test_api_key_required(self):
        """Test the API key required decorator"""

        # Test with API key
        data = json.dumps({
            'api_key': self.app.config.get('API_KEY')})
        response = self.client.post('/_tests/_api/_protected', data=data,
                                    content_type='application/json')

        eq_(response.status_code, 200)

        # Test without API key
        data = json.dumps({})
        response = self.client.post('/_tests/_api/_protected', data=data,
                                    content_type='application/json')

        eq_(response.status_code, 403)


class ViewsTestCase(BaseTestCase):
    def test_feed_view(self):
        """Test the home timeline view in API v2"""
        with self.app.app_context():
            u = user(save=True)
            p = project(save=True)
            for i in range(50):
                if i > 40:
                    p = None
                status(user=u, project=p, save=True)

        response = self.client.get('/api/v2/feed/')
        eq_(response.status_code, 200)
