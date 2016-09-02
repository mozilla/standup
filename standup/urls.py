"""standup URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.contrib import admin

from django_jinja import views


handler403 = views.PermissionDenied.as_view(tmpl_name='errors/403.html')
handler404 = views.PageNotFound.as_view(tmpl_name='errors/404.html')
handler500 = views.ServerError.as_view(tmpl_name='errors/500.html')

urlpatterns = [
    url(r'^api/', include('standup.api.urls')),
    url(r'^admin/', include(admin.site.urls)),

    url(r'', include('standup.status.urls')),

]
