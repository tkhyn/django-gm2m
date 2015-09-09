from bisect import bisect

import django


try:
    # Django 1.8
    from django.db.migrations.state import StateApps

    def is_fake_model(model):
        return isinstance(model._meta.apps, StateApps)
except ImportError:
    # Django 1.7
    def is_fake_model(model):
        return model.__module__ == '__fake__'


try:
    from django.db.models.query_utils import PathInfo
except ImportError:
    # Django < 1.8
    from django.db.models.related import PathInfo

def get_related_model(field):
    try:
        return field.related_model
    except AttributeError:
        # Django < 1.8
        return field.rel.to


if django.VERSION >= (1, 8):

    def add_field(opts, field):
        opts.add_field(field)
        opts._expire_cache()

    def add_related_field(opts, field):
        opts.add_field(field, virtual=True)

else:

    def add_field(opts, field):
        opts.local_many_to_many.insert(bisect(opts.local_many_to_many, field),
                                       field)
        for attr in ('_m2m_cache', '_name_map'):
            try:
                delattr(opts, attr)
            except AttributeError:
                pass

    def add_related_field(opts, field):
        opts.add_virtual_field(field)
