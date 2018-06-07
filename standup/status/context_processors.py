from django.conf import settings

from .models import Project, Team, SiteMessage
from .utils import get_weeks, get_today, get_yesterday


def status(request):
    return {
        'request': request,
        'settings': settings,
        'teams': Team.objects.all(),
        'projects': Project.objects.all(),
        'weeks': get_weeks(),
        'today': get_today(),
        'yesterday': get_yesterday(),
        'messages': SiteMessage.objects.filter(enabled=True),
    }
