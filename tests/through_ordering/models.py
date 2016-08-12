from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

import gm2m

from ..app.models import Project


class Links(models.Model):

    class Meta:
        app_label = 'through_ordering'

    related_objects = gm2m.GM2MField(Project, through='RelLinks')


class RelLinks(models.Model):

    class Meta:
        app_label = 'through_ordering'
        ordering = ('order',)

    links = models.ForeignKey(Links)
    target = GenericForeignKey(ct_field='target_ct', fk_field='target_fk')
    target_ct = models.ForeignKey(ContentType)
    target_fk = models.CharField(max_length=255)

    order = models.IntegerField()
