# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def copy_to_teamusercopy(apps, schema_editor):
    """Copy from TeamUser to TeamUserCopy"""
    TeamUser = apps.get_model('status', 'TeamUser')
    TeamUserCopy = apps.get_model('status', 'TeamUserCopy')

    for teamuser in TeamUser.objects.all():
        if TeamUserCopy.objects.filter(team_id=teamuser.team_id, user_id=teamuser.user_id).count() == 0:
            TeamUserCopy.objects.create(team_id=teamuser.team_id, user_id=teamuser.user_id)
            print('Created %s %s' % (teamuser.team_id, teamuser.user_id))
        else:
            print('Already exists... skipping')


def copy_from_teamusercopy(apps, schema_editor):
    """Copy from TeamUserCopy back to TeamUser"""
    TeamUser = apps.get_model('status', 'TeamUser')
    TeamUserCopy = apps.get_model('status', 'TeamUserCopy')

    for teamusercopy in TeamUserCopy.objects.all():
        if TeamUser.objects.filter(team_id=teamusercopy.team_id, user_id=teamusercopy.user_id).count() == 0:
            TeamUser.objects.create(team_id=teamusercopy.team_id, user_id=teamusercopy.user_id)
            print('Created %s %s' % (teamusercopy.team_id, teamusercopy.user_id))
        else:
            print('Already exists... skipping')


class Migration(migrations.Migration):

    dependencies = [
        ('status', '0012_teamusercopy'),
    ]

    operations = [
        migrations.RunPython(copy_to_teamusercopy, copy_from_teamusercopy)
    ]
