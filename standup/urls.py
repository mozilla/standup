from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth.views import logout

from django_jinja import views


# these will include context processors
handler400 = views.BadRequest.as_view()
handler403 = views.PermissionDenied.as_view()
handler404 = views.PageNotFound.as_view()
handler500 = views.ServerError.as_view()

urlpatterns = [
    url(r'^api/', include('standup.api.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^logout/$', logout, kwargs={'next_page': '/'}, name='auth.logout'),
    url(r'', include('social.apps.django_app.urls', namespace='social')),
    url(r'', include('standup.status.urls')),
]
