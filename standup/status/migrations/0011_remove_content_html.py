# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('status', '0010_populate_slug'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='status',
            options={'ordering': ('-created',), 'verbose_name_plural': 'statuses'},
        ),
        migrations.RemoveField(
            model_name='status',
            name='content_html',
        ),
    ]
