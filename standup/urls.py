from django.conf.urls import include, url
from django.contrib import admin

from django_jinja import views


# these will include context processors
handler400 = views.BadRequest.as_view()
handler403 = views.PermissionDenied.as_view()
handler404 = views.PageNotFound.as_view()
handler500 = views.ServerError.as_view()

urlpatterns = [
    url('^api/', include('standup.api.urls')),
    url('^admin/', include(admin.site.urls)),
    url('', include('standup.status.urls')),

    url('^oidc/', include('mozilla_django_oidc.urls')),
]
