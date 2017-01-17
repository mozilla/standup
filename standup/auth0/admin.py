from django.contrib import admin

from standup.auth0.models import IdToken


@admin.register(IdToken)
class IdTokenAdmin(admin.ModelAdmin):
    fields = ['user', 'id_token', 'expire']
