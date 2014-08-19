from collections import defaultdict

from django.db.models.query import QuerySet
from django.contrib.contenttypes.models import ContentType
from django.utils import six

from .models import SRC_ATTNAME, CT_ATTNAME, PK_ATTNAME


class GM2MSrcQuerySet(QuerySet):
    """
    A QuerySet for GM2M models which yields actual source objects
    instead of GM2M objects when iterated over
    """

    def __init__(self, model=None, query=None, using=None, dest=None):
        super(GM2MSrcQuerySet, self).__init__(model, query, using)
        self.dest = dest

    def _clone(self, klass=None, setup=False, **kwargs):
        clone = super(GM2MSrcQuerySet, self)._clone(klass, setup, **kwargs)
        clone.dest = self.dest
        return clone

    def iterator(self):
        """
        Override to return the actual source objects, not the GM2MObject
        2 queries only by retrieving the pks of the source objects to retrieve
        and then the object themselfs using the 'dest' model
        """
        ids = super(GM2MSrcQuerySet, self).values_list(SRC_ATTNAME, flat=True)

        for obj in self.dest._default_manager.filter(pk__in=ids):
            yield obj


class GM2MTgtQuerySet(QuerySet):
    """
    A QuerySet for GM2M models which yields actual target generic objects
    instead of GM2M objects when iterated over
    """

    def iterator(self):
        """
        Override to return the actual objects, not the GM2MObject
        Fetch the actual objects by content types to optimize database access
        """
        ct_pks = defaultdict(lambda: [])
        for ct, pk \
        in super(GM2MTgtQuerySet, self).values_list(CT_ATTNAME, PK_ATTNAME):
            ct_pks[ct].append(pk)

        for ct, pks in six.iteritems(ct_pks):
            for __, obj in six.iteritems(
                ContentType.objects.get_for_id(ct).model_class()
                                   ._default_manager.in_bulk(pks)):
                yield obj


def create_gm2m_queryset(through, model):
    """
    If target is True, returns a GM2MSrcQuerySet
    If target is False, returns a GM2MTgtQuerySet
    """
    if model:
        return GM2MSrcQuerySet(through, dest=model)
    else:
        return GM2MTgtQuerySet(through)
