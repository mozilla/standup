from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render

from standup.status.models import Status


def home_view(request):
    """Render the front page"""
    status_list = Status.objects.filter(reply_to=None).order_by('-created')
    paginator = Paginator(status_list, 20)

    page = request.GET.get('page')
    try:
        statuses = paginator.page(page)
    except PageNotAnInteger:
        statuses = paginator.page(1)
    except EmptyPage:
        statuses = paginator.page(paginator.num_pages)

    return render(request, 'status/index.html', {
        'statuses': statuses,
    })
