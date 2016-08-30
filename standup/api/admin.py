from django.contrib import admin

from .models import SystemToken


@admin.register(SystemToken)
class SystemTokenAdmin(admin.ModelAdmin):
    list_display = ('token', 'summary', 'enabled', 'contact', 'created')
    list_editable = ('enabled',)
    list_filter = ('enabled',)
    readonly_fields = ('token',)
    ordering = ('created',)
