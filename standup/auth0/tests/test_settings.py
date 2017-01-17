import pytest

from standup.auth0 import settings


class TestListOfStr:
    def test_empty(self):
        assert settings.list_of_str(None) == []
        assert settings.list_of_str('') == []

    def test_handles_sequences(self):
        assert settings.list_of_str(['abc']) == ['abc']
        assert settings.list_of_str(('abc',)) == ['abc']
        assert settings.list_of_str([val for val in 'abc']) == ['a', 'b', 'c']

    def test_one_string(self):
        assert settings.list_of_str('abc') == ['abc']

    def test_multiple_strings(self):
        assert settings.list_of_str('abc,def,ghi') == ['abc', 'def', 'ghi']

    def test_non_sequence_raises_error(self):
        with pytest.raises(AssertionError):
            settings.list_of_str(1)

    def test_non_str_raises_error(self):
        with pytest.raises(AssertionError):
            settings.list_of_str([1, 2, 3])
