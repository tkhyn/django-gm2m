from django.db.models import Model

import gm2m

from ..app.models import Project


class Links(Model):

    related_objects = gm2m.GM2MField(Project)
