from django.db import models
from django.contrib.contenttypes.models import ContentType

import gm2m
from gm2m.compat import GenericForeignKey

from ..app.models import Project


class Links(models.Model):

    related_objects = gm2m.GM2MField(Project, through='RelLinks')


class RelLinks(models.Model):

    links = models.ForeignKey(Links)
    target = GenericForeignKey(ct_field='target_ct', fk_field='target_fk')
    target_ct = models.ForeignKey(ContentType)
    target_fk = models.CharField(max_length=255)

    linked_as = models.CharField(max_length=255)
