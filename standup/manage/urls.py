from django.conf.urls import url

from . import views


urlpatterns = [
    url('^statistics/$', views.statistics_view, name='manage.statistics'),
    url('^errormenow/$', views.errormenow_view, name='manage.errormenow')
]
