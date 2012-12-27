from nose.tools import eq_

from standup.utils import slugify


def test_slugify():
    for text, expected in (
        ('foo', 'foo'),
        ('Foo$$$', 'foo'),
        ('James\' Rifles', 'james-rifles')):

        eq_(slugify(text), expected)
