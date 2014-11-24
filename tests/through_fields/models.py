from django.db import models
from django.contrib.contenttypes.generic import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

import gm2m

from ..app.models import Project


class Links(models.Model):

    related_objects = gm2m.GM2MField(Project, through='RelLinks',
                                     through_fields=('links', 'target'))


class RelLinks(models.Model):

    other_fk = models.ForeignKey(Links, null=True,
                                 related_name='other_rellinks')
    links = models.ForeignKey(Links)

    other_gfk = GenericForeignKey(ct_field='other_gfk_ct',
                                  fk_field='other_gfk_fk')
    other_gfk_ct = models.ForeignKey(ContentType, null=True,
                                     related_name='other_rellinks')
    other_gfk_fk = models.CharField(max_length=255)

    target = GenericForeignKey(ct_field='target_ct', fk_field='target_fk')
    target_ct = models.ForeignKey(ContentType)
    target_fk = models.CharField(max_length=255)

    linked_as = models.CharField(max_length=255)
