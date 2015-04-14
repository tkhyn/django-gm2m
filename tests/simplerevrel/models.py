from django.db import models

import gm2m

from ..app.models import Project


class Links(models.Model):

    related_objects = gm2m.GM2MField(Project)
