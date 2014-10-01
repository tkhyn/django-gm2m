from copy import copy
from bisect import bisect
import inspect

import django
from django.db import models
from django.db.models.options import Options
from django.db.models.fields import related
from django.utils import six


def assert_compat_params(params):

    if django.VERSION < (1, 6):
        params_keys = params.keys()
        assert set(['on_delete', 'on_delete_src', 'on_delete_tgt']) \
            .isdisjoint(params_keys), \
            'Deletion customization is not possible for Django versions ' \
            'prior to 1.6. Please remove the on_delete* arguments or ' \
            'upgrade Django.'

        assert 'db_constraint' not in params_keys, \
            'db_constraint is not supported in Django < 1.6'

        assert 'for_concrete_model' not in params_keys, \
            'for_concrete_model is not supported in Django < 1.6'

try:
    from django.contrib.contenttypes.fields import ForeignObjectRel
except ImportError:
    # Django < 1.7
    from django.contrib.contenttypes.generic import GenericRel

    if django.VERSION < (1, 6):
        class ForeignObjectRel(GenericRel):
            def __init__(self, field, to):
                super(ForeignObjectRel, self).__init__(to)
                self.field = field
    else:
        ForeignObjectRel = GenericRel


if django.VERSION < (1, 6):
    from django.db.models import Field

    class RelatedObject(related.RelatedObject, Field):
        def __init__(self, parent_model, model, field):
            super(RelatedObject, self).__init__(parent_model, model, field)
            self.creation_counter = Field.auto_creation_counter
            Field.auto_creation_counter -= 1

        def related_query_name(self):
            return self.field.related_query_name()

        def m2m_db_table(self):
            try:
                return self.rel.through.db_table
            except AttributeError:
                return None

        def __lt__(self, ro):
            # for python 3.3
            return self.creation_counter < ro.creation_counter
else:
    RelatedObject = related.RelatedObject


if django.VERSION < (1, 6):

    # We need to make sure that queryset related methods are available
    # under the old and new denomination (it is taken care of by
    # django.utils.deprecation.RenameMethodBase in Django >= 1.6)
    # A Metaclass is needed for that purpose

    class GetQSetRenamer(type):
        # inspired from django 1.6's RenameMethodsBase

        renamed_methods = (
            ('get_query_set', 'get_queryset'),
            ('get_prefetch_query_set', 'get_prefetch_queryset')
        )

        def __new__(cls, name, bases, attrs):
            new_class = super(GetQSetRenamer, cls).__new__(cls, name,
                                                           bases, attrs)

            for base in inspect.getmro(new_class):
                for renamed_method in cls.renamed_methods:
                    old_method_name = renamed_method[0]
                    old_method = base.__dict__.get(old_method_name)
                    new_method_name = renamed_method[1]
                    new_method = base.__dict__.get(new_method_name)

                    if not new_method and old_method:
                        # Define the new method if missing
                        setattr(base, new_method_name, old_method)
                    elif not old_method and new_method:
                        # Define the old method if missing
                        setattr(base, old_method_name, new_method)

            return new_class

    mngr_base = six.with_metaclass(GetQSetRenamer, models.Manager)
else:
    mngr_base = models.Manager


class Manager(mngr_base):

    if django.VERSION < (1, 6):

        def _mk_core_filters_norel(self, instance):
            self.core_filters = {'%s__pk' % self.query_field_name: instance.pk}

        def _prefetch_qset_query_norel(self, instances):
            return models.Q(**{'%s_id__in' % self.field_names['src']:
                set(obj.pk for obj in instances)})

    else:

        def _mk_core_filters_norel(self, instance):
            source_field = self.through._meta.get_field(
                               self.field_names['src'])
            self.source_related_fields = source_field.related_fields
            for __, rh_field in self.source_related_fields:
                key = '%s__%s' % (self.query_field_name, rh_field.name)
                self.core_filters[key] = getattr(instance,
                                                 rh_field.attname)

        def _prefetch_qset_query_norel(self, instances):
            query = {}
            for lh_field, rh_field in self.source_related_fields:
                query['%s__in' % lh_field.name] = \
                    set(getattr(obj, rh_field.attname)
                        for obj in instances)
            return models.Q(**query)


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
        from .relations import GM2MRelBase
        f = copy(field)
        f.rel = GM2MRelBase(field, field.rel.to)
        f.rel.on_delete = field.rel.on_delete
        opts.local_many_to_many.insert(bisect(opts.local_many_to_many, f), f)
        for attr in ('_m2m_cache', '_name_map'):
            try:
                delattr(opts, attr)
            except AttributeError:
                pass
    else:
        opts.add_virtual_field(field)


def get_local_related_fields(fk):
    try:
        return fk.local_related_fields
    except AttributeError:  # Django < 1.6
        return (fk,)


def get_foreign_related_fields(fk):
    try:
        return fk.foreign_related_fields
    except AttributeError:  # Django < 1.6
        return (fk.rel.get_related_field(),)


def get_fk_kwargs(field):
    if django.VERSION < (1, 6):
        return {}
    return {'db_constraint': field.rels.db_constraint}


def get_gfk_kwargs(field):
    if django.VERSION < (1, 6):
        return {}
    return {'for_concrete_model': field.rels.for_concrete_model}


def is_swapped(model):
    # falls back to False for Django < 1.6
    return getattr(model._meta, 'swapped', False)
