from collections import defaultdict

from django.db.models import query
from django.utils import six

from .contenttypes import ct as ct_classes, get_content_type


class GM2MTgtQuerySet(query.QuerySet):
    """
    A QuerySet for GM2M models which yields actual target generic objects
    instead of GM2M objects when iterated over
    It can also filter the output by model (= content type)
    """

    def iterator(self):
        """
        Override to return the actual objects, not the GM2MObject
        Fetch the actual objects by content types to optimize database access
        """

        try:
            # Django 1.9
            if self._iterable_class is not query.ModelIterable:
                for v in super(GM2MTgtQuerySet, self).iterator():
                    yield v
                raise StopIteration
        except AttributeError:
            # Django 1.8
            pass

        try:
            del self._related_prefetching
            rel_prefetching = True
        except AttributeError:
            rel_prefetching = False

        ct_attrs = defaultdict(lambda: defaultdict(lambda: []))
        objects = {}
        ordered_ct_attrs = []

        field_names = self.model._meta._field_names
        fk_field = self.model._meta.get_field(field_names['tgt_fk'])

        extra_select = list(self.query.extra_select)

        for vl in self.values_list(field_names['tgt_ct'],
                                   field_names['tgt_fk'],
                                   *extra_select):
            ct = vl[0]
            pk = fk_field.to_python(vl[1])
            ct_attrs[ct][pk].append(vl[2:])
            ordered_ct_attrs.append((ct, pk))

        for ct, attrs in six.iteritems(ct_attrs):
            for pk, obj in six.iteritems(
                ct_classes.ContentType.objects.get_for_id(ct).model_class()
                                      ._default_manager.in_bulk(attrs.keys())):

                pk = fk_field.to_python(pk)

                # we store the through model id in case we are in the process
                # of fetching related objects
                for i, k in enumerate(extra_select):
                    e_list = []
                    for e in attrs[pk]:
                        e_list.append(e[i])
                    setattr(obj, k, e_list)

                if rel_prefetching:
                    # when prefetching related objects, one must yield one
                    # object per through model instance
                    for __ in attrs[pk]:
                        if self.ordered:
                            objects[(ct, pk)] = obj
                        else:
                            yield obj
                    continue

                if self.ordered:
                    objects[(ct, pk)] = obj
                else:
                    yield obj

        if self.ordered:
            for ct, pk in ordered_ct_attrs:
                yield objects[(ct, pk)]

    def filter(self, *args, **kwargs):
        model = kwargs.pop('Model', None)
        models = kwargs.pop('Model__in', set())

        if model:
            models.add(model)

        ctypes = []
        for m in models:
            if isinstance(m, six.string_types):
                m = self.model._meta.apps.get_model(m)
            ctypes.append(get_content_type(m).pk)

        if ctypes:
            kwargs[self.model._meta._field_names['tgt_ct'] + '__in'] = ctypes

        return super(GM2MTgtQuerySet, self).filter(*args, **kwargs)
