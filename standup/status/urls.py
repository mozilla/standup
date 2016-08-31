from django.conf.urls import include, url

from . import views


urlpatterns = [
    url(r'^$', views.home_view, name='status.index'),
    # TODO fix these. Just here so templates will work
    url(r'^feed/$', views.home_view, name='status.index_feed'),
    url(r'^feed/$', views.home_view, name='status.project_feed'),
    url(r'^feed/$', views.home_view, name='status.team_feed'),
    url(r'^feed/$', views.home_view, name='status.user_feed'),
    url(r'^team/(?P<slug>.+)/$', views.team_view, name='status.team'),
    url(r'^project/(?P<slug>.+)/$', views.team_view, name='status.project'),
    url(r'^user/(?P<slug>.+)/$', views.team_view, name='status.user'),
    url(r'^status/(?P<pk>.+)/$', views.status_view, name='status.status'),
    url(r'^weekly/(?P<week>.+)?/?$', views.weekly_view, name='status.weekly'),
    url(r'^profile/$', views.home_view, name='users.profile'),
    url(r'^help/$', views.home_view, name='landings.help'),
]
