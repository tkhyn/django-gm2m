from django.db.models import Model

import gm2m

from ..models import Project


class Links(Model):

    related_objects = gm2m.GM2MField(Project, related_name='related_links')
