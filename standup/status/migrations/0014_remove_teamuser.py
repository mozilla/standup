# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('status', '0013_backup_teamuser'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='teamuser',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='teamuser',
            name='team',
        ),
        migrations.RemoveField(
            model_name='teamuser',
            name='user',
        ),
        migrations.RemoveField(
            model_name='standupuser',
            name='teams',
        ),
        migrations.DeleteModel(
            name='TeamUser',
        ),
    ]
