import django
from django.db.models.fields import Field
from django.db.models.fields.related import ForeignObjectRel
from django.db.models.options import Options


if django.VERSION < (1, 9):
    FIELD_MODEL_ATTR = 'to'

    def to_setter(self, model):
        self.model = model

    ForeignObjectRel.to = property(
        fget=lambda self: self.model,
        fset=to_setter
    )

    Field.remote_field = property(lambda self: self.rel)
else:
    FIELD_MODEL_ATTR = 'model'


if django.VERSION < (1, 10):
    Options.private_fields = property(lambda self: self.virtual_fields)
