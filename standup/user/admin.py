from django.contrib import admin

from standup.user.models import StandupUser, Team


admin.site.register(StandupUser)
admin.site.register(Team)
