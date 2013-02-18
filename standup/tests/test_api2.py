import unittest
from nose.tools import eq_
from standup.apps.api2.helpers import numerify, truth

class HelpersTestCase(unittest.TestCase):
    def test_truth(self):
        """Test the `truth` helper function"""
        assert truth('t')
        assert truth('T')
        assert truth('true')
        assert truth('True')
        assert truth('TRUE')
        assert truth('1')
        assert truth(1)
        assert truth(True)
        assert not truth('f')
        assert not truth(0)
        assert not truth(False)
        assert not truth(None)

    def test_numerify(self):
        """Test the `numerify` helper function"""
        eq_(numerify('1'), 1)
        eq_(numerify(None, 1), 1)
        eq_(numerify('', 1), 1)
        eq_(numerify('25', lower=50), 50)
        eq_(numerify('50', lower=25, upper=75), 50)
        eq_(numerify('75', upper=50), 50)
