# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='StandupUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('slug', models.SlugField(unique=True)),
                ('github_handle', models.CharField(unique=True, max_length=100)),
            ],
            options={
                'ordering': ('user__username',),
            },
        ),
        migrations.AddField(
            model_name='standupuser',
            name='teams',
            field=models.ManyToManyField(to='user.Team'),
        ),
        migrations.AddField(
            model_name='standupuser',
            name='user',
            field=models.OneToOneField(related_name='profile', to=settings.AUTH_USER_MODEL),
        ),
    ]
