from django.shortcuts import render

from standup.status.models import Status


def home_view(request):
    """Render the front page"""
    statuses = Status.objects.filter(reply_to=None).order_by('-created')
    return render(request, 'status/index.html', {
        'statuses': statuses
    })
