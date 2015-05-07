# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import gm2m.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Links',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('related_objects', gm2m.fields.GM2MField()),
            ],
        ),
    ]
