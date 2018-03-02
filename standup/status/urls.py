from django.conf import settings
from django.conf.urls import url

from . import views


SLUG_RE = r'(?P<slug>[-a-zA-Z0-9_@]+)'


urlpatterns = [
    url('^$', views.HomeView.as_view(), name='status.index'),
    url('^team/%s/$' % SLUG_RE, views.TeamView.as_view(), name='status.team'),
    url('^project/%s/$' % SLUG_RE, views.ProjectView.as_view(), name='status.project'),
    url('^user/%s/$' % SLUG_RE, views.UserView.as_view(), name='status.user'),
    url('^status/(?P<pk>\d{1,8})/$', views.StatusView.as_view(), name='status.status'),
    url('^weekly/$', views.WeeklyView.as_view(), name='status.weekly'),
    url('^statusize/$', views.statusize, name='status.statusize'),
    url('^search/$', views.SearchView.as_view(), name='status.search'),

    # profile and signin
    url('^accounts/profile/$', views.ProfileView.as_view(), name='users.profile'),
    url('^accounts/login/$', views.LoginView.as_view(), name='users.loginform'),

    # feeds
    url('^statuses.xml$', views.MainFeed(), name='status.index_feed'),
    url('^user/%s.xml$' % SLUG_RE, views.UserFeed(), name='status.user_feed'),
    url('^team/%s.xml$' % SLUG_RE, views.TeamFeed(), name='status.team_feed'),
    url('^project/%s.xml$' % SLUG_RE, views.ProjectFeed(), name='status.project_feed'),
    url('^statistics/$', views.statistics, name='status.statistics'),

    # csp
    url('^csp-violation-capture$', views.csp_violation_capture),

    # robots
    url('^robots\\.txt$', views.robots_txt),
]

if getattr(settings, 'SITE_TITLE', '').endswith('-stage'):
    # This is for debugging, so we only want it running in dev and in stage environments.
    urlpatterns.append(url('^errormenow$', views.errormenow))
