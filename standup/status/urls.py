from django.conf.urls import url

from . import views


SLUG_RE = r'(?P<slug>[-a-zA-Z0-9_]+)'


urlpatterns = [
    url(r'^$', views.HomeView.as_view(), name='status.index'),
    # TODO fix these. Just here so templates will work
    url(r'^feed/$', views.HomeView.as_view(), name='status.index_feed'),
    url(r'^feed/$', views.HomeView.as_view(), name='status.project_feed'),
    url(r'^feed/$', views.HomeView.as_view(), name='status.user_feed'),
    url(r'^team/{}/$'.format(SLUG_RE), views.TeamView.as_view(), name='status.team'),
    url(r'^team/{}.xml$'.format(SLUG_RE), views.HomeView.as_view(), name='status.team_feed'),
    url(r'^project/{}/$'.format(SLUG_RE), views.team_view, name='status.project'),
    url(r'^user/{}/$'.format(SLUG_RE), views.team_view, name='status.user'),
    url(r'^status/(?P<pk>\d{1,8})/$', views.status_view, name='status.status'),
    url(r'^weekly/(?P<week>\d{4}-\d{2}-\d{2})?/?$', views.weekly_view, name='status.weekly'),
    url(r'^profile/$', views.HomeView.as_view(), name='users.profile'),
    url(r'^help/$', views.HomeView.as_view(), name='landings.help'),
]
