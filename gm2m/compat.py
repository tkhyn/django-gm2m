from copy import copy
from bisect import bisect

import django
from django.db.models.options import Options
from django.db.models.fields.related import RelatedObject
from django.db.utils import DEFAULT_DB_ALIAS
from django.db.models import Q

from .relations import GM2MRel
from .helpers import get_content_type


class GM2MRelatedObject(RelatedObject):

    def __init__(self, parent_model, model, field, rel):
        super(GM2MRelatedObject, self).__init__(parent_model, model, field)
        self.rel = rel
        self.unique = False

    def bulk_related_objects(self, objs, using=DEFAULT_DB_ALIAS):
        """
        Return all objects related to objs
        """

        field_names = self.field.through._meta._field_names
        q = Q()
        for obj in objs:
            # Convert each obj to (content_type, primary_key)
            q = q | Q(**{
                field_names['tgt_ct']: get_content_type(obj),
                field_names['tgt_fk']: obj.pk
            })

        return self.field.through._base_manager.db_manager(using).filter(q)

    if django.VERSION < (1, 6):
        def related_query_name(self):
            return self.field.related_query_name()

        def m2m_db_table(self):
            try:
                return self.rel.through.db_table
            except AttributeError:
                return None

        def __lt__(self, ro):
            # for python 3.3
            return id(self) < id(ro)


def get_model_name(x):
    opts = x if isinstance(x, Options) else x._meta
    try:
        return opts.model_name
    except AttributeError:
        # Django < 1.6
        return opts.object_name.lower()


def add_related_field(opts, field):
    if django.VERSION < (1, 6):
        # hack to enable deletion cascading
        f = copy(field)
        f.rel = GM2MRel(field, field.rel.to)
        opts.local_many_to_many.insert(bisect(opts.local_many_to_many, f), f)
        for attr in ('_m2m_cache', '_name_map'):
            try:
                delattr(opts, attr)
            except AttributeError:
                pass
    else:
        opts.add_virtual_field(field)


def is_swapped(model):
    return getattr(model._meta, 'swapped', False)


def get_queryset(x):
    try:
        return x.get_queryset()
    except AttributeError:
        # Django < 1.6
        return x.get_query_set()
