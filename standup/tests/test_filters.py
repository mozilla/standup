from flask import Flask
from nose.tools import eq_
from standup.filters import format_update, gravatar_url, TAG_TMPL
from standup.tests import BaseTestCase


class FilterTestCase(BaseTestCase):
    def test_tags(self):
        """Test that format update parses tags correctly"""
        with self.app.app_context():
            # Test valid tags.
            for tag in ('#t', '#tag', '#TAG', '#tag123'):
                expected = '%s <div class="tags">%s</div>' % (
                    tag, TAG_TMPL.format('', tag[1:].lower(), tag[1:]))
                eq_(format_update(tag), expected)

            # Test invalid tags.
            for tag in ('#1', '#.abc', '#?abc'):
                eq_(format_update(tag), tag)

    def test_gravatar_url(self):
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
