import hashlib
import re
from urllib.parse import urlencode

import bleach

from django.conf import settings
from django.core.urlresolvers import reverse
from django.templatetags.static import static

from standup.user.models import StandupUser


def dateformat(date, fmt='%Y-%m-%d'):
    def suffix(d):
        suffixes = {1: 'st', 2: 'nd', 3: 'rd'}
        return 'th' if 11 <= d <= 13 else suffixes.get(d % 10, 'th')

    return date.strftime(fmt).replace('{S}', str(date.day) + suffix(date.day))


TAG_TMPL = '{0} <span class="tag tag-{1}">{2}</span>'
BUG_RE = re.compile(r'(bug) #?(\d+)', flags=re.I)
PULL_RE = re.compile(r'(pull|pr) #?(\d+)', flags=re.I)
USER_RE = re.compile(r'(?<=^|(?<=[^\w\-\.]))@([\w-]+)', flags=re.I)
TAG_RE = re.compile(r'(?:^|[^\w\\/])#([a-zA-Z][a-zA-Z0-9_\.-]*)(?:\b|$)')


def format_update(update, project=None):
    # Remove icky stuff.
    formatted = bleach.clean(update, tags=[])

    # Linkify "bug #n" and "bug n" text.
    formatted = BUG_RE.sub(
        r'<a href="http://bugzilla.mozilla.org/show_bug.cgi?id=\2">\1 \2</a>',
        formatted)

    checked = set()
    for slug in USER_RE.findall(formatted):
        if slug in checked:
            continue
        user = StandupUser.objects.filter(slug=slug).first()
        if user:
            url = reverse('status.user', slug=slug)
            at_slug = '@%s' % slug
            formatted = formatted.replace(at_slug,
                                          '<a href="%s">%s</a>' %
                                          (url, at_slug))
        checked.add(slug)

    # Linkify "pull #n" and "pull n" text.
    if project and project.repo_url:
        formatted = PULL_RE.sub(
            r'<a href="%s/pull/\2">\1 \2</a>' % project.repo_url, formatted)

    # Search for tags on the original, unformatted string. A tag must start
    # with a letter.
    tags = TAG_RE.findall(update)
    tags.sort()
    if tags:
        tags_html = ''
        for tag in tags:
            tags_html = TAG_TMPL.format(tags_html, tag.lower(), tag)
        formatted = '%s <div class="tags">%s</div>' % (formatted, tags_html)

    return formatted
