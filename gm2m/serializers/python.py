from django.core.serializers import python
from django.utils.encoding import force_text

from ..fields import GM2MField
from ..contenttypes import get_content_type


class Serializer(python.Serializer):

    def handle_m2m_field(self, obj, field):
        if isinstance(field, GM2MField):
            if field.remote_field.through._meta.auto_created:
                if self.use_natural_foreign_keys:
                    def m2m_value(value):
                        try:
                            natural = value.natural_key()
                        except AttributeError:
                            natural = force_text(value._get_pk_val(),
                                             strings_only=True)
                        return (
                            get_content_type(value).natural_key(),
                            natural
                        )
                else:
                    def m2m_value(value):
                        return (
                            get_content_type(value).natural_key(),
                            force_text(value._get_pk_val(), strings_only=True)
                        )
                self._current[field.name] = [m2m_value(related)
                    for related in getattr(obj, field.name).iterator()]
        else:
            # use normal serialization
            super(Serializer, self).handle_m2m_field(obj, field)

Deserializer = python.Deserializer
