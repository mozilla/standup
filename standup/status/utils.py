import re
from datetime import datetime, timedelta

from django.core.urlresolvers import reverse
from django.utils.timezone import now, make_aware

import bleach

from standup.user.models import StandupUser


def startdate(request):
    dates = request.GET.get('dates')
    day = request.GET.get('day')
    week = request.GET.get('week')
    if dates == '7d':
        return now().date() - timedelta(days=7)
    elif dates == 'today':
        return now().date()
    elif isday(day):
        return get_day(day)
    elif isday(week):
        return week_start(get_day(week))
    return None


def enddate(request):
    day = request.GET.get('day')
    week = request.GET.get('week')
    if isday(day):
        return get_day(day) + timedelta(days=1)
    elif isday(week):
        return week_end(get_day(week))
    return None


def isday(day):
    return day and re.match('^\d{4}-\d{2}-\d{2}$', day)


def get_day(day):
    return make_aware(datetime.strptime(day, '%Y-%m-%d'))


def get_weeks(num_weeks=10):
    weeks = []
    current = now()
    for i in range(num_weeks):
        weeks.append({"start_date": week_start(current),
                      "end_date": week_end(current),
                      "weeks_ago": i})
        current = current - timedelta(7)
    return weeks


def week_start(d):
    """Weeks start on the Monday on or before the given date"""
    d = d - timedelta(d.isoweekday() - 1)
    return make_aware(datetime(d.year, d.month, d.day, 0, 0, 0))


def week_end(d):
    """Weeks start on the Sunday on or after the given date"""
    d = d + timedelta(7 - d.isoweekday())
    return make_aware(datetime(d.year, d.month, d.day, 23, 59, 59))


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
        slug = slug.lstrip('@')
        user = StandupUser.objects.filter(slug=slug).first()
        if user:
            url = reverse('status.user', kwargs={'slug': slug})
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
