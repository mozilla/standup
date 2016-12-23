from django.conf.urls import url
from django.contrib.auth.views import logout

from . import views


urlpatterns = [
    url(r'^auth/logout/?$', logout, kwargs={'next_page': '/'}, name='auth0.logout'),
    url(r'^auth/login/?$', views.Auth0LoginCallback.as_view(), name='auth0.login'),
]
