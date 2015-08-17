from django.db import models

from gm2m import GM2MField


class LocalTask(models.Model):
    pass


class Group(models.Model):

    class Meta:
        app_label = 'multiple_m2m_mig'

    people = GM2MField()


class GroupsTasks(models.Model):

    class Meta:
        app_label = 'multiple_m2m_mig'

    tasks = models.ManyToManyField(LocalTask)
    groups = models.ManyToManyField(Group)
