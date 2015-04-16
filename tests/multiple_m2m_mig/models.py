from django.db import models

from gm2m import GM2MField


class LocalTask(models.Model):
    pass


class Group(models.Model):
    people = GM2MField()


class GroupsTasks(models.Model):
    tasks = models.ManyToManyField(LocalTask)
    groups = models.ManyToManyField(Group)
