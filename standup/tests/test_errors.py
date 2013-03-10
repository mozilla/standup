from flask import abort
from nose.tools import eq_
from standup.tests import BaseTestCase


class ErrorsTestCase(BaseTestCase):
    def __init__(self, *args, **kwargs):
        super(ErrorsTestCase, self).__init__(*args, **kwargs)

        @self.app.route('/oh/no/500')
        def oh_no_500():
            abort(500)

        @self.app.route('/oh/no/403')
        def oh_no_403():
            abort(403)

    def test_error_content_type(self):
        """Make sure the error is the correct content type"""
        response = self.client.get('/does/not/exist')
        eq_(response.status_code, 404)
        eq_(response.content_type, 'text/html; charset=utf-8')

        response = self.client.get('/does/not/exist',
                                   headers=[('Accept', 'application/json')])
        eq_(response.status_code, 404)
        eq_(response.content_type, 'application/json')

    def test_error_handlers(self):
        """Test the standard error handlers"""
        self.app.debug = False

        response = self.client.get('/oh/no/500')
        eq_(response.status_code, 500)
        assert '<div>500: Internal Server Error</div>' in response.data

        response = self.client.get('/does/not/exist')
        eq_(response.status_code, 404)
        assert ('<div class="error-message">404: Not Found</div>'
                in response.data)

        response = self.client.get('/oh/no/403')
        eq_(response.status_code, 403)
        assert ('<div class="error-message">403: Forbidden</div>'
                in response.data)
