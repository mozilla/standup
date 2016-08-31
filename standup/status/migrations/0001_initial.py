# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0002_add_standup_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('slug', models.CharField(unique=True, max_length=100)),
                ('color', models.CharField(max_length=6)),
                ('repo_url', models.URLField(max_length=100)),
            ],
            options={
                'db_table': 'project',
            },
        ),
        migrations.CreateModel(
            name='Status',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('content', models.TextField()),
                ('content_html', models.TextField()),
                ('project', models.ForeignKey(related_name='statuses', to='status.Project')),
                ('reply_to', models.ForeignKey(on_delete=django.db.models.deletion.SET_DEFAULT, default=None, to='status.Status', null=True, blank=True)),
                ('user', models.ForeignKey(related_name='statuses', to='user.StandupUser')),
            ],
            options={
                'db_table': 'status',
            },
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(help_text='Name of the team', max_length=100)),
                ('slug', models.SlugField(unique=True, max_length=100)),
            ],
            options={
                'db_table': 'team',
            },
        ),
        migrations.CreateModel(
            name='TeamUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('team', models.ForeignKey(to='status.Team')),
                ('user', models.ForeignKey(to='user.StandupUser')),
            ],
            options={
                'db_table': 'team_users',
                'unique_together': (('team', 'user'),),
            },
        ),
    ]
