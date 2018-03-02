from django.conf.urls import url

from . import views


urlpatterns = [
    url('^v1/status/(?P<pk>\d{1,8})/$', views.StatusDelete.as_view(), name='api.status-delete'),
    url('^v1/status/', views.StatusCreate.as_view(), name='api.status-create'),
    # FIXME(willkg): Re-enable this after we've reimplemented the UpdateUser view
    # path('v1/user/<slug:username>/', views.UpdateUser.as_view(), name='api.user-update'),
]
