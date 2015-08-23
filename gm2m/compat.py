from copy import copy
from bisect import bisect
import inspect

import django
from django.db import models
from django.db.models.options import Options
from django.db.models.fields import related
from django.utils import six


try:
    from django.apps import apps
    get_model = apps.get_model
except ImportError:
    apps = None
    from django.db.models.loading import get_model

try:
    from django.core import checks
except ImportError:
    checks = None

try:
    # django 1.7+
    from django.db.backends import utils as db_backends_utils
except ImportError:
    from django.db.backends import util as db_backends_utils

try:
    # django 1.7+
    from django.contrib.contenttypes.fields import GenericForeignKey
except ImportError:
    from django.contrib.contenttypes.generic import GenericForeignKey

try:
    # django 1.7+
    from django.db.migrations.state import ModelState
    try:
        # django 1.8
        from django.db.migrations.state import StateApps

        def is_fake_model(model):
            return isinstance(model._meta.apps, StateApps)
    except ImportError:
        # django 1.7
        def is_fake_model(model):
            return model.__module__ == '__fake__'

except ImportError:
    ModelState = None

    def is_fake_model(model):
        return False

try:
    from django.db.models.query_utils import PathInfo
except ImportError:
    # Django < 1.7, reverse query lookup will not be available
    PathInfo = None


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
    from django.db.models.fields.related import ForeignObjectRel
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


try:
    from related import ForeignObject
except ImportError:
    # Django < 1.6
    class ForeignObject(related.RelatedField, related.Field):
        def __init__(self, to, from_fields, to_fields, **kwargs):
            self.from_fields = from_fields
            self.to_fields = to_fields
            super(ForeignObject, self).__init__(**kwargs)

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


def get_related_model(field):
    try:
        return field.related_model
    except AttributeError:
        return field.rel.to


if django.VERSION >= (1, 8):
    def add_related_field(opts, field):
        opts.add_field(field, virtual=True)
elif django.VERSION >= (1, 6):
    def add_related_field(opts, field):
        opts.add_virtual_field(field)
else:
    def add_related_field(opts, field):
        # hack to enable deletion cascading when the collector does not loop on
        # virtual fields
        from .relations import GM2MUnitRelBase
        f = copy(field)
        f.rel = GM2MUnitRelBase(field, field.rel.to)
        f.rel.on_delete = field.rel.on_delete
        opts.local_many_to_many.insert(bisect(opts.local_many_to_many, f), f)
        for attr in ('_m2m_cache', '_name_map'):
            try:
                delattr(opts, attr)
            except AttributeError:
                pass

if django.VERSION >= (1, 8):
    def add_field(opts, field):
        opts.add_field(field)
        opts._expire_cache()
elif django.VERSION < (1, 7):
    def add_field(opts, field):
        opts.add_virtual_field(field)
else:
    def add_field(opts, field):
        opts.local_many_to_many.insert(bisect(opts.local_many_to_many, field),
                                       field)
        for attr in ('_m2m_cache', '_name_map'):
            try:
                delattr(opts, attr)
            except AttributeError:
                pass


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


if django.VERSION < (1, 6):
    def get_fk_kwargs(field):
        return {}

    def get_gfk_kwargs(field):
        return {}
else:
    def get_fk_kwargs(field):
        return {'db_constraint': field.rel.db_constraint}

    def get_gfk_kwargs(field):
        return {'for_concrete_model': field.rel.for_concrete_model}


if django.VERSION < (1, 7):
    def get_meta_kwargs(field):
        return {}
else:
    def get_meta_kwargs(field):
        return {'apps': field.model._meta.apps}


def is_swapped(model):
    # falls back to False for Django < 1.6
    return getattr(model._meta, 'swapped', False)
