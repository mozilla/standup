from django.conf import settings

from standup.user.models import Team
from .models import Project


def status(request):
    return {
        'settings': settings,
        'teams': Team.objects.all(),
        'projects': Project.objects.all(),
    }
