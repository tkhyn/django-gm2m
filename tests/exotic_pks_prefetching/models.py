from django.db import models

import gm2m


class DailyTask(models.Model):

    class Meta:
        app_label = 'exotic_pks_prefetching'

    time = models.TimeField(primary_key=True)


class Day(models.Model):

    class Meta:
        app_label = 'exotic_pks_prefetching'

    date = models.DateField(primary_key=True)
    tasks = gm2m.GM2MField(related_name='days')
