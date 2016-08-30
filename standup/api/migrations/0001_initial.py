# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import standup.api.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SystemToken',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('token', models.CharField(default=standup.api.models.generate_token, help_text='API token for authentication.', max_length=36)),
                ('summary', models.CharField(help_text='System that uses this token.', max_length=200)),
                ('enabled', models.BooleanField(default=False)),
                ('disabled_reason', models.TextField(default='', help_text='Reason this token was disabled/revoked.', blank=True)),
                ('contact', models.CharField(default='', max_length=200, help_text='Contact information for what uses this token. Email address, etc.', blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
