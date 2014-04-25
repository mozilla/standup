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
        with self.app.test_request_context('/'):
            self.app.debug = True
            url = gravatar_url('test@test.com')
            eq_(url, 'http://www.gravatar.com/avatar/'
                     'b642b4217b34b1e8d3bd915fc65c4452?d=mm')

            url = gravatar_url('test@test.com', 200)
            eq_(url, 'http://www.gravatar.com/avatar/'
                     'b642b4217b34b1e8d3bd915fc65c4452?s=200&d=mm')

            self.app.debug = False

            url = gravatar_url('test@test.com')
            eq_(url, 'http://www.gravatar.com/avatar/'
                     'b642b4217b34b1e8d3bd915fc65c4452?d=mm')

            self.app.config['SITE_URL'] = 'http://www.site.com'

            url = gravatar_url('test@test.com')
            eq_(url, 'http://www.gravatar.com/avatar/'
                'b642b4217b34b1e8d3bd915fc65c4452'
                '?d=http%3A%2F%2Fwww.site.com%2Fstatic%2Fimg%2F'
                'default-avatar.png')
