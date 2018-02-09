from django.conf import settings
from django.urls import path

from . import views


urlpatterns = [
    path('', views.HomeView.as_view(), name='status.index'),
    path('team/<slug:slug>/', views.TeamView.as_view(), name='status.team'),
    path('project/<slug:slug>/', views.ProjectView.as_view(), name='status.project'),
    path('user/<slug:slug>/', views.UserView.as_view(), name='status.user'),
    path('status/<int:pk>/', views.StatusView.as_view(), name='status.status'),
    path('weekly/', views.WeeklyView.as_view(), name='status.weekly'),
    path('statusize/', views.statusize, name='status.statusize'),
    path('search/', views.SearchView.as_view(), name='status.search'),

    # profile and signin
    path('accounts/profile/', views.ProfileView.as_view(), name='users.profile'),
    path('accounts/login/', views.LoginView.as_view(), name='users.loginform'),

    # feeds
    path('statuses.xml', views.MainFeed(), name='status.index_feed'),
    path('user/<slug:slug>.xml', views.UserFeed(), name='status.user_feed'),
    path('team/<slug:slug>.xml', views.TeamFeed(), name='status.team_feed'),
    path('project/<slug:slug>.xml', views.ProjectFeed(), name='status.project_feed'),
    path('statistics/', views.statistics, name='status.statistics'),

    # csp
    path('csp-violation-capture', views.csp_violation_capture),

    # robots
    path('robots.txt', views.robots_txt),
]

if getattr(settings, 'SITE_TITLE', '').endswith('-stage'):
    # This is for debugging, so we only want it running in dev and in stage environments.
    urlpatterns.append(path('errormenow', views.errormenow))
