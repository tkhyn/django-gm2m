from django.db import models

import gm2m


class Links(models.Model):

    class Meta:
        app_label = 'stringrevrel'

    related_objects = gm2m.GM2MField('app.Project')
