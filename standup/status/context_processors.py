from django.conf import settings

from .models import Project, Team
from .utils import get_weeks


def status(request):
    return {
        'settings': settings,
        'teams': Team.objects.all(),
        'projects': Project.objects.all(),
        'weeks': get_weeks(),
    }
