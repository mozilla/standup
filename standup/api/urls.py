from django.conf.urls import include, url

from . import views


urlpatterns = [
    url(r'^v1/status/(?P<pk>\d{1,8})/$', views.StatusDelete.as_view(), name='api-status-delete'),
    url(r'^v1/status/', views.StatusPost.as_view(), name='api-status-post'),
    url(r'^v1/user/(?P<username>[a-zA-Z0-9]+)/$', views.UpdateUser.as_view(), name='api-update-user'),
]
