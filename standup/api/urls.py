from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^v1/status/(?P<pk>\d{1,8})/$', views.StatusDelete.as_view(), name='api.status-delete'),
    url(r'^v1/status/', views.StatusCreate.as_view(), name='api.status-create'),
    # FIXME(willkg): Re-enable this after we've reimplemented the UpdateUser view
    # url(r'^v1/user/(?P<username>[a-zA-Z0-9]+)/$', views.UpdateUser.as_view(), name='api.user-update'),
    url(r'v1/messages/$', views.site_messages, name='api.site_messages'),
]
