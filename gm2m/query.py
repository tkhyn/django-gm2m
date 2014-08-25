from collections import defaultdict

from django.db.models.query import QuerySet
from django.contrib.contenttypes.models import ContentType
from django.utils import six


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
        field_names = self.model._meta._field_names
        for ct, pk \
        in super(GM2MTgtQuerySet, self).values_list(field_names['tgt_ct'],
                                                    field_names['tgt_fk']):
            ct_pks[ct].append(pk)

        for ct, pks in six.iteritems(ct_pks):
            for __, obj in six.iteritems(
                ContentType.objects.get_for_id(ct).model_class()
                                   ._default_manager.in_bulk(pks)):
                yield obj
