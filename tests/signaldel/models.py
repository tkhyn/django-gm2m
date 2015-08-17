import django
from django.db import models

import gm2m
from gm2m.deletion import CASCADE_SIGNAL_VETO

from ..app.models import Project

# for Django < 1.6, the on_delete kwarg should NOT be provided
# The deletion tests are then skipped
params = {} if django.VERSION < (1, 6) else {'on_delete': CASCADE_SIGNAL_VETO}


class Links(models.Model):

    class Meta:
        app_label = 'signaldel'

    related_objects = gm2m.GM2MField(Project, **params)
