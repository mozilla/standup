from django.conf.urls import url

from . import views


SLUG_RE = r'(?P<slug>[-a-zA-Z0-9_@]+)'


urlpatterns = [
    url(r'^$', views.home_view, name='status.index'),
    url(r'^team/{}/$'.format(SLUG_RE), views.TeamView.as_view(), name='status.team'),
    url(r'^project/{}/$'.format(SLUG_RE), views.ProjectView.as_view(), name='status.project'),
    url(r'^user/{}/$'.format(SLUG_RE), views.UserView.as_view(), name='status.user'),
    url(r'^status/(?P<pk>\d{1,8})/$', views.StatusView.as_view(), name='status.status'),
    url(r'^weekly/$', views.WeeklyView.as_view(), name='status.weekly'),
    # TODO fix these. Just here so templates will work
    url(r'^profile/$', views.home_view, name='users.profile'),
    url(r'^help/$', views.home_view, name='landings.help'),
    url(r'^statusize/$', views.statusize, name='status.statusize'),
    # feeds
    url(r'^feed/$', views.home_view, name='status.index_feed'),
    url(r'^user/{}.xml$'.format(SLUG_RE), views.home_view, name='status.user_feed'),
    url(r'^team/{}.xml$'.format(SLUG_RE), views.home_view, name='status.team_feed'),
    url(r'^project/{}.xml$'.format(SLUG_RE), views.home_view, name='status.project_feed'),
]
