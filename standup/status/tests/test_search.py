from django.db.models import Q

import pytest

from standup.status.search import (
    generate_query,
    to_tokens,
    unescape,
)


class TestToTokens:
    @pytest.mark.parametrize('text, expected', [
        (u'abc', [u'abc']),
        (u'abc def', [u'abc', u'def']),
        (u'abc OR "def"', [u'abc', u'OR', u'"def"']),
        (u'abc OR "def ghi"', [u'abc', u'OR', u'"def ghi"']),
        (u'abc AND "def ghi"', [u'abc', u'AND', u'"def ghi"']),
    ])
    def test_basic(self, text, expected):
        assert to_tokens(text) == expected

    @pytest.mark.parametrize('text, expected', [
        (u'\\"AND', [u'\\"AND']),
        (u'\\"AND\\"', [u'\\"AND\\"']),
    ])
    def test_escaping(self, text, expected):
        """Escaped things stay escaped"""
        assert to_tokens(text) == expected

    def test_edge_cases(self):
        assert to_tokens(u'AND "def ghi') == [u'AND', u'"def ghi"']


@pytest.mark.parametrize('text, expected', [
    (u'foo', u'foo'),
    (u'\\foo', u'foo'),
    (u'\\\\foo', u'\\foo'),
    (u'foo\\', u'foo'),
    (u'foo\\\\', u'foo\\'),
    (u'foo\\bar', u'foobar'),
    (u'foo\\\\bar', u'foo\\bar'),
])
def test_unescape(text, expected):
    assert unescape(text) == expected


class TestGenerateQuery:
    @pytest.mark.parametrize('field, text, expected', [
        (
            'foo', u'abc',
            Q(foo__icontains=u'abc')
        ),
        (
            'foo', u'abc def',
            Q(foo__icontains=u'abc') | Q(foo__icontains=u'def')
        ),
        (
            'foo', u'abc "def" ghi',
            Q(foo__icontains=u'abc') | Q(foo__icontains=u'def') | Q(foo__icontains=u'ghi')
        ),
        (
            'foo', u'abc AND "def"',
            Q(foo__icontains=u'abc') & Q(foo__icontains=u'def')
        ),
        (
            'foo', u'abc OR "def" AND ghi',
            Q(foo__icontains=u'abc') | (Q(foo__icontains=u'def') & Q(foo__icontains=u'ghi'))
        ),
        (
            'foo', u'abc AND "def" OR ghi',
            Q(foo__icontains=u'abc') & (Q(foo__icontains=u'def') | Q(foo__icontains=u'ghi'))
        ),
        (
            'foo', u'14.1\\" screen',
            # FIXME(willkg): This is probably wrong--probably should be an OR of two clauses
            Q(foo__icontains=u'14.1"') | Q(foo__icontains=u'screen')
        ),

    ])
    def test_basic(self, field, text, expected):
        # NOTE(willkg): We repr the Q objects because otherwise they don't compare. I think this is
        # ok since I think it's order-dependent.
        assert repr(generate_query(field, text)) == repr(expected)

    @pytest.mark.parametrize('field, text, expected', [
        (
            'foo', u'AND "def',
            Q(foo__icontains=u'def')
        ),
        (
            'foo', u'"def" AND',
            Q(foo__icontains=u'def')
        ),
        (
            'foo', u'foo\\bar',
            Q(foo__icontains=u'foobar')
        ),
        (
            'foo', u'foo\\\\bar',
            Q(foo__icontains=u'foo\\bar')
        ),
    ])
    def test_edge_cases(self, field, text, expected):
        # NOTE(willkg): We repr the Q objects because otherwise they don't compare. I think this is
        # ok since I think it's order-dependent.
        assert repr(generate_query(field, text)) == repr(expected)
