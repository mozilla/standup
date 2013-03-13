from nose.tools import eq_

from standup.utils import numerify, slugify, truthify


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


def test_numerify():
    """Test the `numerify` helper function"""
    # Test numeric string
    eq_(numerify('1'), 1)

    # Test numerifying None with default
    eq_(numerify(None, 1), 1)

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
