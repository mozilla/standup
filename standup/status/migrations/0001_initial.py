# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(max_length=100, unique=True)),
                ('slug', models.CharField(max_length=100, unique=True)),
                ('color', models.CharField(max_length=6)),
                ('repo_url', models.URLField(max_length=100)),
            ],
            options={
                'db_table': 'project',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='StandupUser',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('username', models.CharField(max_length=100)),
                ('name', models.CharField(max_length=100, blank=True, null=True)),
                ('slug', models.SlugField(max_length=100, blank=True, null=True)),
                ('email', models.EmailField(max_length=100, blank=True)),
                ('github_handle', models.CharField(max_length=100, blank=True, null=True)),
                ('is_admin', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'user',
            },
        ),
        migrations.CreateModel(
            name='Status',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('content', models.TextField()),
                ('content_html', models.TextField()),
                ('project', models.ForeignKey(to='status.Project', null=True, blank=True,
                                              on_delete=models.SET_DEFAULT, related_name='statuses')),
                ('reply_to', models.ForeignKey(to='status.Status', null=True, blank=True,
                                               on_delete=models.SET_DEFAULT, default=None)),
                ('user', models.ForeignKey(to='status.StandupUser', on_delete=models.SET_DEFAULT,
                                           related_name='statuses')),
            ],
            options={
                'db_table': 'status',
                'ordering': ('-created',),
            },
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(help_text='Name of the team', max_length=100)),
                ('slug', models.SlugField(max_length=100, unique=True)),
            ],
            options={
                'db_table': 'team',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='TeamUser',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('team', models.ForeignKey(to='status.Team', on_delete=models.SET_DEFAULT)),
                ('user', models.ForeignKey(to='status.StandupUser', on_delete=models.SET_DEFAULT)),
            ],
            options={
                'db_table': 'team_users',
            },
        ),
        migrations.AddField(
            model_name='standupuser',
            name='teams',
            field=models.ManyToManyField(to='status.Team', related_name='users', through='status.TeamUser'),
        ),
        migrations.AlterUniqueTogether(
            name='teamuser',
            unique_together=set([('team', 'user')]),
        ),
    ]
