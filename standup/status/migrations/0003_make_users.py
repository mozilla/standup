# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.hashers import make_password
from django.db import migrations
from django.db.models.signals import post_save


def create_system_users(apps, schema_editor):
    StandupUser = apps.get_model('status', 'StandupUser')
    User = apps.get_model('auth', 'User')
    post_save.disconnect(User)
    for user in StandupUser.objects.all():
        new_user = User(
            username=user.username,
            email=user.email or '',
            is_staff=user.is_admin,
        )
        # set an unusable and random password
        new_user.password = make_password(None)
        new_user.save()

        ghh = user.github_handle
        if ghh.startswith('https://github.com/'):
            user.github_handle = ghh[19:]

        user.user = new_user
        user.save()


class Migration(migrations.Migration):

    dependencies = [
        ('status', '0002_standupuser_user'),
    ]

    operations = [
        migrations.RunPython(create_system_users, lambda x, y: None),
    ]
