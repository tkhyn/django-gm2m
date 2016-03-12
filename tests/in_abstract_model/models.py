from django.db import models

import gm2m


class LinksBase(models.Model):

    class Meta:
        abstract = True
        app_label = 'in_abstract_model'

    related_objects = gm2m.GM2MField('app.Project')


class BasicLinks(LinksBase):
    pass


class EnhancedLinks(LinksBase):
    pass
