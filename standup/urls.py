from django.contrib import admin
from django.urls import include, path

from django_jinja import views


# these will include context processors
handler400 = views.BadRequest.as_view()
handler403 = views.PermissionDenied.as_view()
handler404 = views.PageNotFound.as_view()
handler500 = views.ServerError.as_view()

urlpatterns = [
    path('api/', include('standup.api.urls')),
    path('admin/', admin.site.urls),
    path('', include('standup.status.urls')),

    path('oidc/', include('mozilla_django_oidc.urls')),
]
