from django.db import models

import gm2m
from gm2m.deletion import CASCADE_SIGNAL_VETO

from ..app.models import Project


class Links(models.Model):

    class Meta:
        app_label = 'signaldel'

    related_objects = gm2m.GM2MField(Project, on_delete=CASCADE_SIGNAL_VETO)
