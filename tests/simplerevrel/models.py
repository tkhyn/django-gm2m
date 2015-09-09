from django.db import models

import gm2m

from ..app.models import Project


class Links(models.Model):

    class Meta:
        app_label = 'simplerevrel'

    name = models.CharField(max_length=255, blank=True)
    related_objects = gm2m.GM2MField(Project)
