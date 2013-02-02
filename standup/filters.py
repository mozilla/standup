import hashlib
import re
from bleach import clean
from flask import url_for
from standup import settings
from urllib import urlencode

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
    m = hashlib.md5(email.lower())
    hash = m.hexdigest()
    url = 'http://www.gravatar.com/avatar/' + hash

    qs = {}

    if getattr(settings, 'DEBUG', False) or not hasattr(settings, 'SITE_URL'):
        qs['d'] = 'mm'
    else:
        qs['d'] = settings.SITE_URL + url_for(
            'static', filename='img/default-avatar.png')

    if size:
        qs['s'] = size

    url += '?' + urlencode(qs)
    return url


def format_update(update, project=None):
    def set_target(attrs,
                   new=False):
        attrs['target'] = '_blank'
        return attrs

    # Remove icky stuff.
    formatted = clean(update, tags=[])

    # Linkify "bug #n" and "bug n" text.
    formatted = re.sub(r'(bug) #?(\d+)',
        r'<a href="http://bugzilla.mozilla.org/show_bug.cgi?id=\2">\1 \2</a>',
        formatted, flags=re.I)

    # Linkify "pull #n" and "pull n" text.
    if project and project.repo_url:
        formatted = re.sub(r'(pull|pr) #?(\d+)',
            r'<a href="%s/pull/\2">\1 \2</a>' % project.repo_url, formatted,
            flags=re.I)

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
