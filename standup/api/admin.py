from django.contrib import admin

from .models import SystemToken


@admin.register(SystemToken)
class SystemTokenAdmin(admin.ModelAdmin):
    pass
