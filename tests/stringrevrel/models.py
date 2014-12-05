from django.db.models import Model

import gm2m


class Links(Model):

    related_objects = gm2m.GM2MField('app.Project')
