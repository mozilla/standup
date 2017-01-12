# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('status', '0007_migration_irc_nick'),
    ]

    operations = [
        migrations.AlterField(
            model_name='standupuser',
            name='github_handle',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
    ]
