# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('status', '0005_add_team_user_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='standupuser',
            name='irc_nick',
            field=models.CharField(help_text='IRC nick for this particular user', max_length=100, null=True, unique=True, blank=True),
        ),
        migrations.AlterField(
            model_name='standupuser',
            name='github_handle',
            field=models.CharField(max_length=100, null=True, unique=True, blank=True),
        ),
        migrations.AlterField(
            model_name='standupuser',
            name='slug',
            field=models.SlugField(max_length=100, null=True, unique=True, blank=True),
        ),
    ]
