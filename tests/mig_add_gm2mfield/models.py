from django.db import models

from gm2m import GM2MField

from ..app.models import Task


# this is for bug #33, where a circular relation is needed
class Project(models.Model):

    class Meta:
        app_label = 'mig_add_gm2mfield'

    owner = models.ForeignKey('User')


class User(models.Model):

    class Meta:
        app_label = 'mig_add_gm2mfield'

    name = models.CharField(blank=True, default='', max_length=100)
    # mig1: items = GM2MField(Project)
    # mig2: items = GM2MField(Task, Project)
