# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def teamusercopy_to_teams(apps, schema_editor):
    StandupUser = apps.get_model('status', 'StandupUser')
    Team = apps.get_model('status', 'Team')
    TeamUserCopy = apps.get_model('status', 'TeamUserCopy')

    for tuc in TeamUserCopy.objects.all():
        # Get the user and team
        suser = StandupUser.objects.get(id=tuc.user_id)
        team = Team.objects.get(id=tuc.team_id)

        # Add the team to the user
        suser.teams.add(team)
        print('Adding %s to team %s' % (suser.id, team.id))


def noop(apps, schema_editor):
    return


class Migration(migrations.Migration):

    dependencies = [
        ('status', '0015_team_users'),
    ]

    operations = [
        migrations.RunPython(teamusercopy_to_teams, noop)
    ]
