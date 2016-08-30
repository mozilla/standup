from django.contrib import admin

from standup.status.models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    fields = (('name', 'slug'), 'color', 'repo_url')
    list_display = ['name', 'color']
    list_editable = ['color']
    prepopulated_fields = {'slug': ['name']}
    search_fields = ['name', 'repo_url']

