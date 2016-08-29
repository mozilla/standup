# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('status', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='status',
            name='project',
            field=models.ForeignKey(to='status.Project', related_name='statuses', null=True),
        ),
    ]
