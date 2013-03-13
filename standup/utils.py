import re

import simplejson as json
from flask import Response, request
from unidecode import unidecode


_PUNCT_RE = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')


def slugify(text, delim=u'-'):
    """Generates an ASCII-only slug."""
    result = []
    for word in _PUNCT_RE.split(text.lower()):
        result.extend(unidecode(unicode(word)).split())
    return unicode(delim.join(result))


def json_requested():
    """Check if json is the preferred output format for the request."""
    best = request.accept_mimetypes.best_match(
        ['application/json', 'text/html'])
    return (best == 'application/json' and
            request.accept_mimetypes[best] >
            request.accept_mimetypes['text/html'])


def jsonify(obj):
    """Dump an object to JSON and create a Response object from the dump.
    Unlike Flask's native implementation, this works on lists.
    """
    dump = json.dumps(obj)
    return Response(dump, mimetype='application/json')


def truthify(s):
    """Returns a boolean from a string"""
    try:
        return str(s).lower() in ['true', 't', '1']
    except (TypeError, ValueError, UnicodeEncodeError):
        return False


def numerify(s, default=None, lower=None, upper=None):
    """Converts a string to an integer"""
    if s is None:
        s = default
    num = int(s)
    if lower is not None and num < lower:
        num = lower
    if upper is not None and num > upper:
        num = upper
    return num
