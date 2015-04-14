import django
from django.db import models
from django.db.models.deletion import DO_NOTHING

import gm2m

from ..app.models import Project

# for Django < 1.6, the on_delete kwarg should NOT be provided
# The deletion tests are then skipped
params = {} if django.VERSION < (1, 6) else {'on_delete': DO_NOTHING}


class Links(models.Model):

    related_objects = gm2m.GM2MField(Project, **params)
