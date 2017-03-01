# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('status', '0011_remove_content_html'),
    ]

    operations = [
        migrations.CreateModel(
            name='TeamUserCopy',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('team_id', models.IntegerField()),
                ('user_id', models.IntegerField()),
            ],
        ),
    ]
