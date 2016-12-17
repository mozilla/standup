import collections
import datetime
import gc
import json
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.syndication.views import Feed
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.http import Http404
from django.http import (HttpResponse, HttpResponseBadRequest,
                         HttpResponseForbidden, HttpResponseRedirect)
from django.shortcuts import render
from django.utils.feedgenerator import Atom1Feed
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, TemplateView, UpdateView, View

from raven.contrib.django.models import client
import requests
from requests.exceptions import ConnectTimeout, ReadTimeout

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


class ProfileView(UpdateView):
    template_name = 'users/profile.html'
    form_class = ProfileForm
    success_url = '/profile/'
    new_profile = False

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            messages.error(request, 'You must be signed in to view your profile. '
                                    'Please sign in and try again.')
            return HttpResponseRedirect(reverse('users.loginform'))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['new_profile'] = self.new_profile
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


class LogoutView(View):
    """Logs a user out"""
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            messages.info(request, 'You are not logged in.')
        else:
            # FIXME(willkg): Should require a csrf.
            logout(request)
            messages.info(request, 'You have been logged out.')
        return HttpResponseRedirect('/')


def username_generator(base):
    """Generates usernames using a base plus some count"""
    yield base

    count = 2
    while True:
        yield '%s%d' % (base, count)


def get_or_create_user(email, name=None):
    """Retrieves or creates a User instance

    :arg str email: the email of the user
    :arg str name: the name of the user (or none)

    :returns: User instance

    """
    User = get_user_model()
    try:
        # Try matching on email first--that's our canonical lookup.
        return User.objects.get(email__iexact=email)

    except User.DoesNotExist:
        try:
            # Didn't match on email, so this might be an older account that's never had a profile.
            # So try to match on username, but only if the email field is empty.
            return User.objects.get(email='', username__iexact=email.split('@', 1)[0])

        except User.DoesNotExist:
            # Didn't match email or username, so this is probably a new user.
            username_base = name or email.split('@', 1)[0]
            password = User.objects.make_random_password()

            for username in username_generator(username_base):
                try:
                    user = User.objects.create(
                        username=username,
                        email=email,
                        password=password,
                    )
                    user.save()
                    return user

                except IntegrityError:
                    pass


def get_or_create_profile(user):
    """Retrieves or creates a StandupUser instance

    If this creates a new StandupUser, it makes sure that the StandupUser has a unique slug.

    :arg user User: a User instance

    :returns: StandupUser instance

    """
    try:
        profile = user.profile
    except StandupUser.DoesNotExist:
        profile = StandupUser.objects.create(
            user=user
        )

    if not profile.slug:
        for slug in username_generator(user.username):
            try:
                profile.slug = slug
                profile.save()
            except IntegrityError:
                pass
    return profile


class Auth0LoginCallback(View):
    def get(self, request):
        """Auth0 redirects to this view so we can log the user in

        This handles creating User and StandupUser objects if needed.

        """
        code = request.GET.get('code', '')

        if not code:
            if request.GET.get('error'):
                messages.error(
                    request,
                    'Unable to sign in because of an error from Auth0. ({msg})'.format(
                        msg=request.GET.get('error_description', request.GET['error'])
                    )
                )
                return HttpResponseRedirect(reverse('users.loginform'))
            return HttpResponseBadRequest('Missing "code"')

        json_header = {
            'content-type': 'application/json'
        }

        token_url = 'https://{domain}/oauth/token'.format(domain=settings.AUTH0_DOMAIN)

        token_payload = {
            'client_id': settings.AUTH0_CLIENT_ID,
            'client_secret': settings.AUTH0_CLIENT_SECRET,
            'redirect_uri': settings.AUTH0_CALLBACK_URL,
            'code': code,
            'grant_type': 'authorization_code'
        }

        try:
            token_info = requests.post(
                token_url,
                headers=json_header,
                json=token_payload,
                timeout=settings.AUTH0_PATIENCE_TIMEOUT
            ).json()

            if not token_info.get('access_token'):
                messages.error(
                    request,
                    'Unable to authenticate with Auth0 at this time. Please refresh to '
                    'try again.'
                )
                return HttpResponseRedirect(reverse('users.loginform'))

            user_url = 'https://{domain}/userinfo?access_token={access_token}'.format(
                domain=settings.AUTH0_DOMAIN, access_token=token_info['access_token']
            )

            user_info = requests.get(user_url).json()

        except (ConnectTimeout, ReadTimeout):
            messages.error(
                request,
                'Unable to authenticate with Auth0 at this time. Please wait a bit '
                'and try again.'
            )
            return HttpResponseRedirect(reverse('users.loginform'))

        # Get or create User instance using email address and nickname
        user = get_or_create_user(user_info['email'], user_info.get('nickname'))

        # If inactive, add message and redirect to login page
        if not user.is_active:
            messages.error(
                request,
                'This user account is inactive.'
            )
            return HttpResponseRedirect(reverse('users.loginform'))

        # Make sure they have a profile
        get_or_create_profile(user)

        # Log the user in
        # FIXME(willkg): This is sort of a lie--should we have our own backend?
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)

        # FIXME(willkg): Should we send them to the front page or their user page?
        return HttpResponseRedirect(reverse('status.index'))


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


@cache_page(60 * 60 * 24 * 365)
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
    hours_24 = datetime.datetime.now() - datetime.timedelta(hours=24)
    week = datetime.datetime.now() - datetime.timedelta(days=7)

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
