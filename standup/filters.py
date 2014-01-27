import hashlib
import re
from urllib import urlencode

from bleach import clean
from flask import current_app, url_for


TAG_TMPL = '{0} <span class="tag tag-{1}">{2}</span>'


def register_filters(app):
    app.add_template_filter(dateformat)
    app.add_template_filter(gravatar_url)
    app.add_template_filter(format_update)


def dateformat(date, fmt='%Y-%m-%d'):
    def suffix(d):
        suffixes = {1: 'st', 2: 'nd', 3: 'rd'}
        return 'th' if 11 <= d <= 13 else suffixes.get(d % 10, 'th')

    return date.strftime(fmt).replace('{S}', str(date.day) + suffix(date.day))


def gravatar_url(email, size=None):
    app = current_app
    m = hashlib.md5(email.lower())
    hash = m.hexdigest()
    url = 'http://www.gravatar.com/avatar/' + hash

    qs = {}

    # gravatar default URLs must be publicly accessible, so 'localhost' ones
    # are a no-go
    if app.debug or not 'SITE_URL' in app.config or \
                       'localhost' in app.config.get('SITE_URL'):
        qs['d'] = 'mm'
    else:
        qs['d'] = app.config.get('SITE_URL') + url_for(
            'static', filename='img/default-avatar.png')

    if size:
        qs['s'] = size

    url += '?' + urlencode(qs)
    return url


def format_update(update, project=None):
    BUG_RE = re.compile(r'(bug) #?(\d+)', flags=re.I)
    PULL_RE = re.compile(r'(pull|pr) #?(\d+)', flags=re.I)

    # Remove icky stuff.
    formatted = clean(update, tags=[])

    # Linkify "bug #n" and "bug n" text.
    formatted = BUG_RE.sub(
        r'<a href="http://bugzilla.mozilla.org/show_bug.cgi?id=\2">\1 \2</a>',
        formatted)

    # Linkify "pull #n" and "pull n" text.
    if project and project.repo_url:
        formatted = PULL_RE.sub(
            r'<a href="%s/pull/\2">\1 \2</a>' % project.repo_url, formatted)

    # Search for tags on the original, unformatted string. A tag must start
    # with a letter.
    tags = re.findall(r'(?:^|[^\w\\/])#([a-zA-Z][a-zA-Z0-9_\.-]*)(?:\b|$)',
                      update)
    tags.sort()
    if tags:
        tags_html = ''
        for tag in tags:
            tags_html = TAG_TMPL.format(tags_html, tag.lower(), tag)
        formatted = '%s <div class="tags">%s</div>' % (formatted, tags_html)

    return formatted
