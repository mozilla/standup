# flake8: noqa

import pytest


@pytest.mark.skip('This is busted--fix me.')
def test_gravatar_url():
    """Test that the gravatar url is generated correctly"""
    # Note: We make a fake Flask app for this.
    app = Flask(__name__)

    with app.test_request_context('/'):
        app.debug = True
        url = gravatar_url('test@example.com')
        eq_(url,
            'http://www.gravatar.com/avatar/'
            '55502f40dc8b7c769880b10874abc9d0?d=mm')

        url = gravatar_url('test@example.com', 200)
        eq_(url,
            'http://www.gravatar.com/avatar/'
            '55502f40dc8b7c769880b10874abc9d0?s=200&d=mm')

        app.debug = False

        url = gravatar_url('test@example.com')
        eq_(url,
            'http://www.gravatar.com/avatar/'
            '55502f40dc8b7c769880b10874abc9d0?d=mm')

        app.config['SITE_URL'] = 'http://www.site.com'

        url = gravatar_url('test@example.com')
        eq_(url,
            'http://www.gravatar.com/avatar/'
            '55502f40dc8b7c769880b10874abc9d0'
            '?d=http%3A%2F%2Fwww.site.com%2Fstatic%2Fimg%2F'
            'default-avatar.png')
