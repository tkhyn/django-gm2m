from django.db.models.fields.related import ReverseManyRelatedObjectsDescriptor
from django.utils.functional import cached_property

from .managers import create_gm2m_related_manager


class GM2MDescriptor(ReverseManyRelatedObjectsDescriptor):
    """
    Provides a generic many-to-many descriptor to make the related manager
    available from the source model class
    """

    @property
    def through(self):
        return self.field.through

    @cached_property
    def related_manager_cls(self):
        return create_gm2m_related_manager()

    def __get__(self, instance, instance_type=None):
        if instance is None:
            return self
        return self.related_manager_cls(instance, self.field.through)

    def __set__(self, instance, value):
        manager = self.__get__(instance)
        manager.clear()
        manager.add(*value)
