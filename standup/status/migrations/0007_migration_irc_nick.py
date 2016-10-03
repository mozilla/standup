# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def migrate_irc_nick(apps, schema_editor):
    """Copy the User.username into the StandupUser.irc_nick field because this is what the irc bot in
    Standup v1 used to match.

    """
    StandupUser = apps.get_model('status', 'StandupUser')
    for suser in StandupUser.objects.all():
        suser.irc_nick = suser.user.username
        suser.save()


def wipe_irc_nick(apps, schema_editor):
    """Wipe the StandupUser.irc_nick field contents"""
    StandupUser = apps.get_model('status', 'StandupUser')
    for suser in StandupUser.objects.all():
        suser.irc_nick = None
        suser.save()


class Migration(migrations.Migration):

    dependencies = [
        ('status', '0006_add_irc_nick'),
    ]

    operations = [
        migrations.RunPython(migrate_irc_nick, wipe_irc_nick),
    ]
