import collections
import datetime
import gc
import json
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.syndication.views import Feed
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.urlresolvers import reverse
from django.http import Http404
from django.http import (HttpResponse, HttpResponseBadRequest,
                         HttpResponseForbidden, HttpResponseRedirect)
from django.shortcuts import render
from django.utils.feedgenerator import Atom1Feed
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, TemplateView, UpdateView

import pytz
from raven.contrib.django.models import client

from standup.status.forms import StatusizeForm, ProfileForm
from standup.status.models import Status, Team, Project, StandupUser
from standup.status.search import generate_query
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
        qs = Status.objects.filter(reply_to=None).select_related('project', 'user')
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
        qs = Status.objects.filter(pk=self.kwargs['pk'])
        if not qs:
            raise Http404()

        return qs


class UserView(PaginateStatusesMixin, DetailView):
    template_name = 'status/user.html'
    model = StandupUser
    context_object_name = 'suser'

    def get_status_queryset(self):
        return self.object.statuses.filter(reply_to=None).select_related('project', 'user')


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


class SearchView(PaginateStatusesMixin, TemplateView):
    template_name = 'status/search.html'

    def get_status_queryset(self):
        query = self.request.GET.get('query')
        if not query:
            return []

        return Status.objects.filter(generate_query('content', query))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['query'] = self.request.GET.get('query', '')
        return ctx


class ProfileView(UpdateView):
    template_name = 'users/profile.html'
    form_class = ProfileForm
    success_url = '/accounts/profile/'
    new_profile = False

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            messages.error(request, 'You must be signed in to view your profile. '
                                    'Please sign in and try again.')
            return HttpResponseRedirect(reverse('users.loginform'))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Mark that this is a new profile if the profile has no name
        if not self.request.user.profile.name:
            ctx['new_profile'] = True
        return ctx

    def get_object(self, queryset=None):
        return self.request.user.profile

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Something went wrong. Please try again.')
        return super().form_invalid(form)


class LoginView(TemplateView):
    template_name = 'users/login.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            messages.info(request, 'You are already signed in.')
            return HttpResponseRedirect('/')
        return super().get(request, *args, **kwargs)


# FEEDS


class StatusesFeed(Feed):
    feed_type = Atom1Feed
    feed_limit = 50
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
        content = str(item.htmlify())
        if item.project:
            content = '<h3>%s</h3>%s' % (item.project.name, content)

        return content


class MainFeed(StatusesFeed):
    title = 'All status updates'

    def items(self):
        return Status.objects.filter(reply_to=None).select_related('project', 'user')[:self.feed_limit]


class UserFeed(StatusesFeed):
    obj_model = StandupUser

    def title(self, obj):
        return 'Updates by {}'.format(obj.slug)

    def items(self, obj):
        return obj.statuses.filter(reply_to=None).select_related('project', 'user')[:self.feed_limit]


class ProjectFeed(StatusesFeed):
    obj_model = Project

    def title(self, obj):
        return 'Updates for {}'.format(obj.name)

    def items(self, obj):
        return obj.statuses.filter(reply_to=None).select_related('project', 'user')[:self.feed_limit]


class TeamFeed(StatusesFeed):
    obj_model = Team

    def title(self, obj):
        return 'Updates from {}'.format(obj.name)

    def items(self, obj):
        return obj.statuses().select_related('project', 'user')[:self.feed_limit]


# RANDOM STUFF


@csrf_exempt
@require_POST
def csp_violation_capture(request):
    # HT @glogiotatidis https://github.com/mozmar/lumbergh/pull/180/
    if not settings.CSP_REPORT_ENABLE:
        # mitigation option for a flood of violation reports
        return HttpResponse()

    data = client.get_data_from_request(request)
    data.update({
        'level': logging.INFO,
        'logger': 'CSP',
    })
    try:
        csp_data = json.loads(request.body.decode())
    except ValueError:
        # Cannot decode CSP violation data, ignore
        return HttpResponseBadRequest('Invalid CSP Report')

    try:
        blocked_uri = csp_data['csp-report']['blocked-uri']
    except KeyError:
        # Incomplete CSP report
        return HttpResponseBadRequest('Incomplete CSP Report')

    client.captureMessage(message='CSP Violation: {}'.format(blocked_uri),
                          data=data)

    return HttpResponse('Captured CSP violation, thanks for reporting.')


def robots_txt(request):
    if settings.ROBOTS_ALLOW:
        content = ''
    else:
        content = 'User-agent: *\nDisallow: /'

    return HttpResponse(content, content_type='text/plain')


def errormenow(request):
    # This is an intentional error designed to kick up the error page because otherwise it's
    # difficult to test.
    1 / 0  # noqa


def statistics(request):
    """Show health statistics for the system"""
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

    groups['Infra'] = collections.OrderedDict([
        ('Objects count', len(gc.get_objects())),
    ])

    return render(request, 'status/statistics.html', {
        'statsitems': groups,
    })
