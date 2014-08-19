from django.db import models

import gm2m


class Links(models.Model):
    related_objects = gm2m.GM2MField()
