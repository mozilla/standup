import re
from datetime import date, datetime, timedelta

def paginate(statuses, page=1, startdate=None, enddate=None):
    from standup.apps.status.models import Status
    if startdate:
        statuses = statuses.filter(Status.created >= startdate)
    if enddate:
        statuses = statuses.filter(Status.created <= enddate)
    return statuses.paginate(int(page))


def startdate(request):
    dates = request.args.get('dates')
    day = request.args.get('day')
    if dates == '7d':
        return date.today() - timedelta(days=7)
    elif dates == 'today':
        return date.today()
    elif isday(day):
        return day(day)
    return None


def enddate(request):
    day = request.args.get('day')
    if isday(day):
        return day(day) + timedelta(days=1)
    return None


def isday(day):
    return day and re.match('^\d{4}-\d{2}-\d{2}$', day)


def day(day):
    return datetime.strptime(day, '%Y-%m-%d')
