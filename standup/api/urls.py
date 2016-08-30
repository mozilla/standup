from django.conf.urls import include, url

from . import views


urlpatterns = [
    url(r'^v1/status/', views.StatusPost.as_view(), name='api-status-post')
]
