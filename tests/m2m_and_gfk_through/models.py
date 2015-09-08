"""
Test case for issue #5
Django 1.8 migration problems with combined M2M and GM2M relations
"""

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

import gm2m


class GM2MLinks(models.Model):

    class Meta:
        app_label = 'm2m_and_gfk_through'

    sources = gm2m.GM2MField()


class MembershipThrough(models.Model):

    class Meta:
        app_label = 'm2m_and_gfk_through'

    possibly = models.ForeignKey('Membership')
    link = models.ForeignKey(GM2MLinks)


class Membership(models.Model):

    class Meta:
        app_label = 'm2m_and_gfk_through'

    many_link = models.ManyToManyField(GM2MLinks, through=MembershipThrough)


class RandomData(models.Model):
    """
    Even though this seems completely unrelated to any of the other models,
    just adding a GFK causes the problems to surface with an M2M-Through
    """

    class Meta:
        app_label = 'm2m_and_gfk_through'

    object_id = models.PositiveIntegerField()
    content_type = models.ForeignKey(ContentType)
    my_gfk = GenericForeignKey('content_type', 'object_id')
