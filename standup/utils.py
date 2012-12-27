import re
from unidecode import unidecode


_PUNCT_RE = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')


def slugify(text, delim=u'-'):
    """Generates an ASCII-only slug."""
    result = []
    for word in _PUNCT_RE.split(text.lower()):
        result.extend(unidecode(word).split())
    return unicode(delim.join(result))
