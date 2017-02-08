# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('status', '0008_github_handle_fixes'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='standupuser',
            name='github_handle',
        ),
    ]
