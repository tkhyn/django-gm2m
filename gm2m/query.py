from collections import defaultdict

from django.db.models.query import QuerySet
from django.contrib.contenttypes.models import ContentType

from .models import CT_ATTNAME, PK_ATTNAME


class GM2MQuerySet(QuerySet):
    """
    A QuerySet for GM2M models which yields actual objects instead of GM2M
    objects when iterated over
    """

    def iterator(self):
        """
        Override to return the actual objects, not the GM2MObject
        Fetch the actual objects by content types to optimize database access
        """
        ct_pks = defaultdict(lambda: [])
        for ct, pk \
        in super(GM2MQuerySet, self).values_list(CT_ATTNAME, PK_ATTNAME):
            ct_pks[ct].append(pk)

        for ct, pks in ct_pks.iteritems():
            for __, obj in ContentType.objects.get_for_id(ct).model_class() \
                                              ._default_manager.in_bulk(pks) \
                                              .iteritems():
                yield obj
