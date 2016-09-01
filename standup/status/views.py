import re
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.views.generic import DetailView
from django.views.generic import TemplateView

from standup.status.models import Status, Team, Project
from standup.status.utils import enddate, startdate


class PaginateStatusesMixin(object):
    def paginate_statuses(self, per_page=20):
        qs = self.get_status_queryset()
        page = self.request.GET.get('page')
        paginator = Paginator(qs, per_page)
        try:
            statuses = paginator.page(page)
        except PageNotAnInteger:
            statuses = paginator.page(1)
        except EmptyPage:
            statuses = paginator.page(paginator.num_pages)

        return statuses

    def get_status_queryset(self):
        qs = Status.objects.filter(reply_to=None)
        start = startdate(self.request)
        if start:
            end = enddate(self.request)
            if not end:
                end = start

            qs = qs.filter(created__range=(start, end))

        return qs

    def get_context_data(self, **kwargs):
        cxt = super().get_context_data(**kwargs)
        cxt['statuses'] = self.paginate_statuses()
        return cxt


class HomeView(PaginateStatusesMixin, TemplateView):
    template_name = 'status/index.html'


class WeeklyView(PaginateStatusesMixin, TemplateView):
    template_name = 'status/weekly.html'

    def get_status_queryset(self):
        qs = super().get_status_queryset()
        return qs.order_by('user_id', '-created')


class TeamView(PaginateStatusesMixin, DetailView):
    template_name = 'status/team.html'
    model = Team
    context_object_name = 'team'

    def get_status_queryset(self):
        return self.object.statuses()


class ProjectView(PaginateStatusesMixin, DetailView):
    template_name = 'status/project.html'
    model = Project
    context_object_name = 'project'

    def get_status_queryset(self):
        return self.object.statuses.filter(reply_to=None)


def status_view(request, pk):
    return 'team'


home_view = HomeView.as_view()
