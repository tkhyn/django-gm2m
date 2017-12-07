"""
This module patches older versions of django to expose properties that were
renamed in later versions.

This could of course create problems if another app patches these properties
differently but it's the likeliness of this to happen is so low that it should
not be an issue
"""


import django
from django.db.models.fields import Field
from django.db.models.fields.related import ForeignObjectRel
from django.db.models.options import Options
from django.db.models import query
from django.utils import six


try:
    from django.db.models.fields.related import lazy_related_operation
except ImportError:
    # Django 1.8
    from django.db.models.fields.related import add_lazy_relation

    def lazy_related_operation(function, model, *related_models, **kwargs):

        field_name, field = list(six.iteritems(kwargs))[0]

        def operation(field, related, local):
            return function(local, related, **{field_name: field})

        add_lazy_relation(model, field, related_models[0], operation)


if django.VERSION < (1, 9):
    FIELD_MODEL_ATTR = 'to'

    def model_setter(self, model):
        self.to = model

    ForeignObjectRel.model = property(
        fget=lambda self: self.to,
        fset=model_setter,
        doc='= self.to - added by django-gm2m'
    )

    Field.remote_field = property(lambda self: self.rel,
                                  doc='= self.rel - added by django-gm2m')

else:
    # django >= 1.9
    FIELD_MODEL_ATTR = 'model'


if django.VERSION < (1, 10):
    Options.private_fields = property(
        lambda self: self.virtual_fields,
        doc='= self.virtual_fields - added by django-gm2m'
    )

    class ModelIterable(object):
        def __init__(self, queryset, chunked_fetch=False):
            self.queryset = queryset
            self.chunked_fetch = chunked_fetch

else:
    # django >= 1.10
    ModelIterable = query.ModelIterable

    if django.VERSION < (1, 11):
        # monkey-patch needed to make BaseIterable in dj1.10 accept
        # chunked_fetch argument
        __init__0 = query.BaseIterable.__init__
        def __init__(self, queryset, chunked_fetch=False):
            __init__0(self, queryset)
            self.chunked_fetch = chunked_fetch
        query.BaseIterable.__init__ = __init__
