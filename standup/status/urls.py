from django.conf import settings
from django.conf.urls import url
from django.views.decorators.cache import cache_page

from . import views


SLUG_RE = r'(?P<slug>[-a-zA-Z0-9_@]+)'
cache_feed = cache_page(settings.CACHE_FEEDS_SECONDS)

urlpatterns = [
    url(r'^$', views.HomeView.as_view(), name='status.index'),
    url(r'^team/{}/$'.format(SLUG_RE), views.TeamView.as_view(), name='status.team'),
    url(r'^project/{}/$'.format(SLUG_RE), views.ProjectView.as_view(), name='status.project'),
    url(r'^user/{}/$'.format(SLUG_RE), views.UserView.as_view(), name='status.user'),
    url(r'^status/(?P<pk>\d{1,8})/$', views.StatusView.as_view(), name='status.status'),
    url(r'^weekly/$', views.WeeklyView.as_view(), name='status.weekly'),
    url(r'^profile/$', views.ProfileView.as_view(), name='users.profile'),
    url(r'^new-profile/$', views.ProfileView.as_view(new_profile=True),
        name='users.new_profile'),
    url(r'^statusize/$', views.statusize, name='status.statusize'),

    # auth
    url(r'^auth/login-form$', views.LoginView.as_view(), name='users.loginform'),
    url(r'^auth/logout$', views.LogoutView.as_view(), name='users.logout'),
    url(r'^auth/login$', views.Auth0LoginCallback.as_view(), name='auth0.login'),

    # feeds
    url(r'^statuses.xml$', cache_feed(views.MainFeed()), name='status.index_feed'),
    url(r'^user/{}.xml$'.format(SLUG_RE), cache_feed(views.UserFeed()), name='status.user_feed'),
    url(r'^team/{}.xml$'.format(SLUG_RE), cache_feed(views.TeamFeed()), name='status.team_feed'),
    url(r'^project/{}.xml$'.format(SLUG_RE), cache_feed(views.ProjectFeed()),
        name='status.project_feed'),
    url(r'^statistics/$', views.statistics, name='status.statistics'),

    # csp
    url(r'^csp-violation-capture$', views.csp_violation_capture),

    # robots
    url(r'^robots\.txt$', views.robots_txt),
]

if getattr(settings, 'SITE_TITLE', '').endswith('-stage'):
    # This is for debugging, so we only want it running in dev and in stage environments.
    urlpatterns.append(url(r'^errormenow$', views.errormenow))
