from django.contrib import admin

from standup.status.models import Project, Team, StandupUser, Status


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    fields = (('name', 'slug'), 'color', 'repo_url')
    list_display = ['name', 'color']
    list_editable = ['color']
    prepopulated_fields = {'slug': ['name']}
    search_fields = ['name', 'repo_url']


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    fields = ['name', 'slug']
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ['name']}


@admin.register(StandupUser)
class StandupUserAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'irc_nick']
    search_fields = ['name', 'slug', 'irc_nick']
    filter_horizontal = ['teams']


@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'project', 'content']
    search_fields = ['content']
    # FIXME(willkg): We want to make reply_to go away and having it causes the page to
    # load *all* the statuses in the db which is insane.
    exclude = ['reply_to']
