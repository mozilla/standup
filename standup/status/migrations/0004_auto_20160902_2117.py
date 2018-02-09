# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('status', '0003_make_users'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='standupuser',
            name='email',
        ),
        migrations.RemoveField(
            model_name='standupuser',
            name='is_admin',
        ),
        migrations.RemoveField(
            model_name='standupuser',
            name='username',
        ),
        migrations.AlterField(
            model_name='standupuser',
            name='user',
            field=models.OneToOneField(
                to=settings.AUTH_USER_MODEL,
                on_delete=models.CASCADE,
                related_name='profile'
            ),
        ),
    ]
