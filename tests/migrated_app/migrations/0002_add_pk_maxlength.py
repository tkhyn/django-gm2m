# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import gm2m.fields


class Migration(migrations.Migration):

    dependencies = [
        ('migrated_app', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='links',
            name='related_objects',
            field=gm2m.fields.GM2MField(pk_maxlength=50),
        ),
    ]
