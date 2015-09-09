from django.db import models

from gm2m import GM2MField

from ..app.models import Project, Task


class User(models.Model):

    class Meta:
        app_label = 'mig_add_gm2mfield'

    name = models.CharField(blank=True, default='', max_length=100)
    # items = GM2MField(Project, Task)
