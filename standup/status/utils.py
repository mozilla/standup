import re
from datetime import datetime, timedelta

from django.utils.timezone import now, make_aware


def get_today():
    return now().date()


def get_yesterday():
    return get_today() - timedelta(days=1)


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
