from django.contrib import admin

from standup.user.models import StandupUser, Team


@admin.register(StandupUser)
class StandupUserAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'slug', 'github_handle']
    filter_horizontal = ['teams']


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    fields = ['name', 'slug']
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ['name']}
