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
    FIELD_MODEL_ATTR = 'model'


if django.VERSION < (1, 10):
    Options.private_fields = property(
        lambda self: self.virtual_fields,
        doc='= self.virtual_fields - added by django-gm2m'
    )
