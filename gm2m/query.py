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

        try:
            del self._related_prefetching
            rel_prefetching = True
        except AttributeError:
            rel_prefetching = False

        ct_attrs = defaultdict(lambda: defaultdict(lambda: []))
        field_names = self.model._meta._field_names

        extra_select = list(self.query.extra_select)

        for vl in self.values_list(field_names['tgt_ct'],
                                   field_names['tgt_fk'],
                                   *extra_select):
            ct = vl[0]
            pk = vl[1]
            ct_attrs[ct][pk].append(vl[2:])

        for ct, attrs in six.iteritems(ct_attrs):
            for pk, obj in six.iteritems(
                ContentType.objects.get_for_id(ct).model_class()
                           ._default_manager.in_bulk(attrs.keys())):

                # we store the through model id in case we are in the process
                # of fetching related objects
                for i, k in enumerate(extra_select):
                    e_list = []
                    for e in attrs[str(pk)]:
                        e_list.append(e[i])
                    setattr(obj, k, e_list)

                if rel_prefetching:
                    # when prefetching related objects, one must yield one
                    # object per through model instance
                    for __ in attrs[str(pk)]:
                        yield obj
                    continue

                yield obj
