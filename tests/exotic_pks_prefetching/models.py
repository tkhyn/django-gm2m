from django.db import models

import gm2m


class DailyTask(models.Model):
    time = models.TimeField(primary_key=True)


class Day(models.Model):
    date = models.DateField(primary_key=True)
    tasks = gm2m.GM2MField(related_name='days')
