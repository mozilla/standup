from django.contrib import messages
from django.contrib.syndication.views import Feed
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import HttpResponseForbidden
from django.http import HttpResponseRedirect
from django.utils.feedgenerator import Atom1Feed
from django.views.decorators.http import require_POST
from django.views.generic import DetailView
from django.views.generic import TemplateView
from django.views.generic import UpdateView

from standup.status.forms import StatusizeForm, ProfileForm
from standup.status.models import Status, Team, Project, StandupUser
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


class StatusView(PaginateStatusesMixin, TemplateView):
    template_name = 'status/status.html'

    def get_status_queryset(self):
        return Status.objects.filter(pk=self.kwargs['pk'])


class UserView(PaginateStatusesMixin, DetailView):
    template_name = 'status/user.html'
    model = StandupUser
    context_object_name = 'suser'

    def get_status_queryset(self):
        return self.object.statuses.filter(reply_to=None)


@require_POST
def statusize(request):
    if not request.user.is_authenticated():
        return HttpResponseForbidden()

    data = request.POST.dict()
    data['user'] = request.user.profile.id
    form = StatusizeForm(data)
    if form.is_valid():
        form.save()
    else:
        messages.error(request, 'Form error. Please try again.')

    referrer = request.META.get('HTTP_REFERER', '/')
    return HttpResponseRedirect(data.get('redirect_to', referrer))


class ProfileView(UpdateView):
    template_name = 'users/profile.html'
    form_class = ProfileForm
    success_url = '/profile/'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            messages.error(request, 'You must be logged-in to view your profile. '
                                    'Please login and try again.')
            return HttpResponseRedirect('/')
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return self.request.user.profile

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Something went wrong. Please try again.')
        return super().form_invalid(form)


# FEEDS


class StatusesFeed(Feed):
    feed_type = Atom1Feed
    feed_limit = 200
    obj_model = None

    def get_object(self, request, slug=None):
        if self.obj_model is None:
            return None

        return self.obj_model.objects.get(slug=slug)

    def link(self, obj):
        if obj is None:
            return '/'

        return obj.get_absolute_url()

    def item_title(self, item):
        return 'From {} at {}'.format(item.user.slug,
                                      item.created.strftime('%I:%M%p %Z'))

    def item_pubdate(self, item):
        return item.created

    def item_description(self, item):
        content = item.htmlify()
        if item.project:
            content = '<h3>%s</h3>%s' % (item.project.name, content)

        return content


class MainFeed(StatusesFeed):
    title = 'All status updates'

    def items(self):
        return Status.objects.filter(reply_to=None)[:self.feed_limit]


class UserFeed(StatusesFeed):
    obj_model = StandupUser

    def title(self, obj):
        return 'Updates by {}'.format(obj.slug)

    def items(self, obj):
        return obj.statuses.filter(reply_to=None)[:self.feed_limit]


class ProjectFeed(StatusesFeed):
    obj_model = Project

    def title(self, obj):
        return 'Updates for {}'.format(obj.name)

    def items(self, obj):
        return obj.statuses.filter(reply_to=None)[:self.feed_limit]


class TeamFeed(StatusesFeed):
    obj_model = Team

    def title(self, obj):
        return 'Updates from {}'.format(obj.name)

    def items(self, obj):
        return obj.statuses()[:self.feed_limit]
