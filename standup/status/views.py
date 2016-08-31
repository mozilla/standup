from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.views.generic import DetailView
from django.views.generic import TemplateView

from standup.status.models import Status, Team


def paginate_statuses(qs, page, per_page=20):
    paginator = Paginator(qs, per_page)
    try:
        statuses = paginator.page(page)
    except PageNotAnInteger:
        statuses = paginator.page(1)
    except EmptyPage:
        statuses = paginator.page(paginator.num_pages)

    return statuses


class HomeView(TemplateView):
    template_name = 'status/index.html'

    def get_context_data(self, **kwargs):
        cxt = super().get_context_data(**kwargs)
        status_list = Status.objects.filter(reply_to=None)
        cxt['statuses'] = paginate_statuses(status_list, self.request.GET.get('page'))
        return cxt


class TeamView(DetailView):
    template_name = 'status/team.html'
    model = Team
    context_object_name = 'team'

    def get_context_data(self, **kwargs):
        cxt = super().get_context_data(**kwargs)
        statuses = paginate_statuses(self.object.statuses(),
                                     self.request.GET.get('page'))
        cxt['statuses'] = statuses
        return cxt


def team_view(request, slug):
    return 'team'


def status_view(request, pk):
    return 'team'


def weekly_view(request, week=None):
    pass
