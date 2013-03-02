from nose.tools import eq_

from standup.utils import slugify, truthify


def test_slugify():
    """Test the slugify function"""
    for text, expected in ((u'foo', 'foo'), (u'Foo$$$', 'foo'),
                           (u'James\' Rifles', 'james-rifles')):

        eq_(slugify(text), expected)


def test_truthify():
    """Test the truthify function"""
    # True
    eq_(truthify('t'), True)
    eq_(truthify('T'), True)
    eq_(truthify('1'), True)
    eq_(truthify('True'), True)
    eq_(truthify('true'), True)
    eq_(truthify('TRUE'), True)
    eq_(truthify(True), True)
    eq_(truthify(1), True)

    # False
    eq_(truthify(0), False)
    eq_(truthify(False), False)
    eq_(truthify('0'), False)
    eq_(truthify('f'), False)
    eq_(truthify('False'), False)
    eq_(truthify('y'), False)
    eq_(truthify(None), False)
    eq_(truthify(u'\x80'), False)
