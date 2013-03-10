from nose.tools import eq_

from standup.utils import slugify


def test_slugify():
    for text, expected in ((u'foo', 'foo'), (u'Foo$$$', 'foo'),
                           (u'James\' Rifles', 'james-rifles')):

        eq_(slugify(text), expected)
