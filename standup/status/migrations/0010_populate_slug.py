# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.utils.text import slugify


def add_slugs(apps, schema_editor):
    StandupUser = apps.get_model('status', 'StandupUser')

    # For every StandupUser that has a slug that's either null or '', we want to populate the slug
    # with a slugified version of the username.
    susers = StandupUser.objects.filter(models.Q(slug=None) | models.Q(slug=''))
    print('%d users need slug fixing.' % susers.count())
    for suser in StandupUser.objects.filter(models.Q(slug=None) | models.Q(slug='')):
        print('Fixing %s: %s...' % (suser.id, suser.name))
        username = suser.user.username
        slug = slugify(username)
        suser.slug = slug
        suser.save()


class Migration(migrations.Migration):
    dependencies = [
        ('status', '0009_remove_standupuser_github_handle'),
    ]

    operations = [
        migrations.RunPython(add_slugs, lambda x, y: None),
    ]
