# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models  # noqa

# Note: This was written when we needed to migrate the Standup db from the old schema to the new
# one. We don't need to do that anymore and this migration prevents contributors from creating fresh
# databases, so I'm commenting it out.

# def fill_teamuser_ids(apps, schema_editor):
#     """Fill in unique IDs for TeamUser rows"""
#     TeamUser = apps.get_model('status', 'TeamUser')
#     index = 0
#     for tu in TeamUser.objects.all():
#         index += 1
#         tu.id = index
#         tu.save()


class Migration(migrations.Migration):

    dependencies = [
        ('status', '0004_auto_20160902_2117'),
    ]

    operations = [
        # migrations.AddField(
        #     model_name='teamuser',
        #     name='id',
        #     field=models.AutoField(serialize=False, auto_created=True, verbose_name='ID')
        # ),
        # migrations.RunPython(fill_teamuser_ids, reverse_code=lambda x, y: None),
        # migrations.AlterField(
        #     model_name='teamuser',
        #     name='id',
        #     field=models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)
        # )
    ]
