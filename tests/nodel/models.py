from django.db import models
from django.db.models.deletion import DO_NOTHING

import gm2m

from ..app.models import Project


class Links(models.Model):

    class Meta:
        app_label = 'nodel'

    related_objects = gm2m.GM2MField(Project, on_delete=DO_NOTHING)
