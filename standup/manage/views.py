import collections
import datetime

import pytz

from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render

from standup.status.models import Status, Team, StandupUser


def require_superuser(fun):
    def authorize_user(user):
        return user.is_active and user.is_superuser

    return user_passes_test(authorize_user)(fun)


@require_superuser
def errormenow_view(request):
    # This is an intentional error designed to kick up the error page because
    # otherwise it's difficult to test.
    1 / 0  # noqa


@require_superuser
def statistics_view(request):
    """Show health statistics for the system

    .. Note::

       This is an "admin" view, so it uses Django templates.

    """
    hours_24 = datetime.datetime.now(tz=pytz.UTC) - datetime.timedelta(hours=24)
    week = datetime.datetime.now(tz=pytz.UTC) - datetime.timedelta(days=7)

    groups = collections.OrderedDict()

    groups['Standup users'] = collections.OrderedDict([
        ('Team count', Team.objects.count()),
        ('User count', StandupUser.objects.count()),
        ('New users in last 24 hours', StandupUser.objects.filter(user__date_joined__gte=hours_24).count()),
        ('Active users (posted in last week)',
         StandupUser.objects.filter(id__in=Status.objects.filter(created__gte=week).values('user__id')).count()),
    ])

    groups['Standup status'] = collections.OrderedDict([
        ('Status count', Status.objects.count()),
        ('Status in last 24 hours', Status.objects.filter(created__gte=hours_24).count()),
        ('Status in last week', Status.objects.filter(created__gte=week).count()),
    ])

    context = {
        'title': 'Site statistics',
        'statsitems': groups
    }

    return render(request, 'admin/statistics.html', context)
