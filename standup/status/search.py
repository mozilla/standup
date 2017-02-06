from django.db.models import Q


# FIXME(willkg): This ignores the variety of other whitespace characters in unicode.
WHITESPACE = u' \t\r\n'


def to_tokens(text):
    """Breaks the search text into tokens"""
    in_quotes = False
    escape = False

    tokens = []
    token = []

    for c in text:
        if c == u'\\':
            escape = True
            token.append(c)
            continue

        if in_quotes:
            if not escape and c == u'"':
                in_quotes = False
            token.append(c)

        elif not escape and c == u'"':
            in_quotes = True
            token.append(c)

        elif c in WHITESPACE:
            if token:
                tokens.append(u''.join(token))
                token = []

        else:
            token.append(c)

        escape = False

    if in_quotes:
        # Finish off a missing quote
        if token:
            token.append(u'"')
        else:
            tokens[-1] = tokens[-1] + u'"'

    if token:
        # Add last token
        tokens.append(u''.join(token))

    return tokens


class ParseError(Exception):
    pass


def unescape(text):
    """Unescapes text

    >>> unescape(u'abc')
    u'abc'
    >>> unescape(u'\\abc')
    u'abc'
    >>> unescape(u'\\\\abc')
    u'\\abc'

    """
    # Note: We can ditch this and do it in tokenizing if tokenizing
    # returned typed tokens rather than a list of strings.
    new_text = []
    escape = False
    for c in text:
        if not escape and c == u'\\':
            escape = True
            continue

        new_text.append(c)
        escape = False

    return u''.join(new_text)


def build_match(field, token):
    return Q(**{'%s__icontains' % field: unescape(token)})


def build_match_phrase(field, token):
    return Q(**{'%s__icontains' % field: unescape(token)})


def build_or(clauses):
    if len(clauses) == 1:
        return clauses[0]

    q = clauses[0]
    for clause in clauses[1:]:
        q = q | clause
    return q


def build_and(clauses):
    if len(clauses) == 1:
        return clauses[0]

    q = clauses[0]
    for clause in clauses[1:]:
        q = q & clause
    return q


def parse_match(field, tokens):
    """Parses a match or match_phrase node

    :arg field: the field we're querying on
    :arg tokens: list of tokens to consume

    :returns: list of match clauses
    """
    clauses = []

    while tokens and tokens[-1] not in (u'OR', u'AND'):
        token = tokens.pop()

        if token.startswith(u'"'):
            clauses.append(build_match_phrase(field, token[1:-1]))
        else:
            clauses.append(build_match(field, token))

    return clauses


def parse_oper(field, lhs, tokens):
    """Parses a single bool query

    :arg field: the field we're querying on
    :arg lhs: the clauses on the left hand side
    :arg tokens: list of tokens to consume

    :returns: bool query
    """
    token = tokens.pop()
    rhs = parse_query(field, tokens)

    if token == u'OR':
        lhs.extend(rhs)
        return build_or(lhs)
    elif token == u'AND':
        lhs.extend(rhs)
        return build_and(lhs)

    # Note: This probably will never get reached given the way
    # parse_match slurps. If the code were changed, it's possible this
    # might be triggerable.
    raise ParseError('Not an oper token: {0}'.format(token))


def parse_query(field, tokens):
    """Parses a match or query

    :arg field: the field we're querying on
    :arg tokens: list of tokens to consume

    :returns: list of clauses
    """
    match_clauses = parse_match(field, tokens)
    if tokens:
        return [parse_oper(field, match_clauses, tokens)]
    return match_clauses


def generate_query(field, text):
    """Parses the search text and returns a Q

    This tries to handle parse errors. If the text is unparseable, it
    returns a single Q.

    :arg field: the field to search
    :arg text:  the user's search text

    :return: Q

    It uses a recursive descent parser with this grammar::

        query = match | match oper
        oper  = "AND" query |
                "OR" query
        match = token ... |
                '"' token '"'

    If it encounters a parse error, it attempts to recover, but if it
    can't, then it just returns a single match query.

    """
    # Build the Q tree data structure bottom up.
    tokens = to_tokens(text)
    tokens.reverse()

    try:
        clauses = parse_query(field, tokens)
    except ParseError:
        return build_match(field, text)

    if len(clauses) > 1:
        return build_or(clauses)

    return clauses[0]
