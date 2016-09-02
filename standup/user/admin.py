from django.contrib import admin

from standup.user.models import StandupUser


@admin.register(StandupUser)
class StandupUserAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'slug', 'github_handle']
    search_fields = ['slug', 'github_handle', 'user__first_name', 'user__last_name']
