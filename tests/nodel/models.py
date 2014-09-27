import django
from django.db.models import Model
from django.db.models.deletion import DO_NOTHING

import gm2m

from ..app.models import Project

# for Django < 1.6, the default value CASCADE should be used for on_delete to
# prevent errors during imports, and the tests are skipped
params = {} if django.VERSION < (1, 6) else {'on_delete': DO_NOTHING}


class Links(Model):

    related_objects = gm2m.GM2MField(Project, **params)
