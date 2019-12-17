from collections import defaultdict

from django.db.models.query import ModelIterable, QuerySet

from .contenttypes import ct as ct_classes, get_content_type


class GM2MTgtQuerySetIterable(ModelIterable):

    def __iter__(self):
        """
        Override to return the actual objects, not the GM2MObject
        Fetch the actual objects by content types to optimize database access
        """

        qs = self.queryset

        try:
            del qs._related_prefetching
            rel_prefetching = True
        except AttributeError:
            rel_prefetching = False

        ct_attrs = defaultdict(lambda: defaultdict(lambda: []))
        objects = {}
        ordered_ct_attrs = []

        field_names = qs.model._meta._field_names
        fk_field = qs.model._meta.get_field(field_names['tgt_fk'])

        extra_select = list(qs.query.extra_select)

        for vl in qs.values_list(field_names['tgt_ct'],
                                 field_names['tgt_fk'],
                                 *extra_select):
            ct = vl[0]
            pk = fk_field.to_python(vl[1])
            ct_attrs[ct][pk].append(vl[2:])
            ordered_ct_attrs.append((ct, pk))

        for ct, attrs in ct_attrs.items():
            for pk, obj in ct_classes.ContentType.objects.get_for_id(ct).\
                    model_class()._default_manager.in_bulk(attrs.keys()).\
                    items():

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
                        if qs.ordered:
                            objects[(ct, pk)] = obj
                        else:
                            yield obj
                    continue

                if qs.ordered:
                    objects[(ct, pk)] = obj
                else:
                    yield obj

        if qs.ordered:
            for ct, pk in ordered_ct_attrs:
                yield objects[(ct, pk)]


class GM2MTgtQuerySet(QuerySet):
    """
    A QuerySet for GM2M models which yields actual target generic objects
    instead of GM2M objects when iterated over
    It can also filter the output by model (= content type)
    """

    def __init__(self, model=None, query=None, using=None, hints=None):
        super(GM2MTgtQuerySet, self).__init__(model, query, using, hints)

        if self._iterable_class is ModelIterable:
            self._iterable_class = GM2MTgtQuerySetIterable

    def filter(self, *args, **kwargs):
        model = kwargs.pop('Model', None)
        models = kwargs.pop('Model__in', set())

        if model:
            models.add(model)

        ctypes = []
        for m in models:
            if isinstance(m, str):
                m = self.model._meta.apps.get_model(m)
            ctypes.append(get_content_type(m).pk)

        if ctypes:
            kwargs[self.model._meta._field_names['tgt_ct'] + '__in'] = ctypes

        return super(GM2MTgtQuerySet, self).filter(*args, **kwargs)
