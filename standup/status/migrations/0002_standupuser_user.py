# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('status', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='standupuser',
            name='user',
            field=models.OneToOneField(
                null=True,
                to=settings.AUTH_USER_MODEL,
                on_delete=models.CASCADE,
                related_name='profile'
            ),
        ),
    ]
