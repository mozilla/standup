from django.urls import path

from . import views


urlpatterns = [
    path('v1/status/<int:pk>/', views.StatusDelete.as_view(), name='api.status-delete'),
    path('v1/status/', views.StatusCreate.as_view(), name='api.status-create'),
    # FIXME(willkg): Re-enable this after we've reimplemented the UpdateUser view
    # path('v1/user/<slug:username>/', views.UpdateUser.as_view(), name='api.user-update'),
    path('v1/messages/', views.site_messages, name='api.site_messages'),
]
