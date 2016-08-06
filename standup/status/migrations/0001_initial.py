# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('slug', models.CharField(unique=True, max_length=100)),
                ('color', models.CharField(max_length=6)),
                ('repo_url', models.URLField()),
            ],
        ),
        migrations.CreateModel(
            name='Status',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('content', models.TextField()),
                ('content_html', models.TextField()),
                ('project', models.ForeignKey(related_name='statuses', to='status.Project')),
                ('reply_to', models.ForeignKey(on_delete=django.db.models.deletion.SET_DEFAULT, to='status.Status', null=True, blank=True, default=None)),
                ('user', models.ForeignKey(related_name='statuses', to='user.StandupUser')),
            ],
        ),
    ]
