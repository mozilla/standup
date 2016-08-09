from django.conf import settings


def status(request):
    return {
        'settings': settings,
    }
