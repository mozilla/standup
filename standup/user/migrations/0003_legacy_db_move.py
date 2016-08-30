# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def migrate_legacy_users(apps, schema_editor):
    LegacyUser = apps.get_model('user', 'LegacyUser')
    StandupUser = apps.get_model('user', 'StandupUser')
    User = apps.get_model('auth', 'User')
    for old_user in LegacyUser.objects.all():
        names = old_user.name.split(maxsplit=1)
        new_user = User.objects.create(
            username=old_user.username,
            first_name=names[0],
            last_name=names[1] if len(names) > 1 else '',
            email=old_user.email or '',
            is_staff=old_user.is_admin,
            is_superuser=old_user.is_admin,
        )
        ghh = old_user.github_handle
        if ghh.startswith('https://github.com/'):
            ghh = ghh[19:]

        StandupUser.objects.create(
            id=old_user.id,
            user=new_user,
            slug=old_user.slug,
            github_handle=ghh,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0002_add_standup_user'),
    ]

    operations = [
        migrations.RunPython(migrate_legacy_users, lambda x, y: None)
    ]
