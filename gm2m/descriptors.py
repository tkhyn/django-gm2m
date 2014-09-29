from django.db.models.fields.related import ManyRelatedObjectsDescriptor, \
                                            ReverseManyRelatedObjectsDescriptor
from django.utils.functional import cached_property


from .managers import create_gm2m_related_manager
from .compat import get_model_name


class GM2MRelatedDescriptor(ManyRelatedObjectsDescriptor):
    """
    Provides a generic many-to-many descriptor to make the related manager
    available from the source model class
    """

    def __init__(self, related, rel):
        super(GM2MRelatedDescriptor, self).__init__(related)
        self.rel = rel

    @cached_property
    def related_manager_cls(self):
        return create_gm2m_related_manager(
            self.rel.to._default_manager.__class__)

    def __get__(self, instance, instance_type=None):
        if instance is None:
            return self
        return self.related_manager_cls(
            field=self.related.field,
            model=self.related.model,
            instance=instance,
            through=self.rel.through,
            query_field_name=get_model_name(self.related.field.rels.through),
            field_names=self.related.field.rels.through._meta._field_names,
            prefetch_cache_name=self.related.field.related_query_name(),
        )

    def __set__(self, instance, value):
        manager = self.__get__(instance)
        manager.clear()
        manager.add(*value)


class ReverseGM2MRelatedDescriptor(ReverseManyRelatedObjectsDescriptor):
    """
    Provides a generic many-to-many descriptor to make the source manager
    available from a target model class
    """

    def add_relation(self, *args, **kwargs):
        return self.field.add_relation(*args, **kwargs)

    @cached_property
    def related_manager_cls(self):
        return create_gm2m_related_manager()

    def __get__(self, instance, instance_type=None):
        if instance is None:
            return self
        field_names = self.field.rels.through._meta._field_names
        return self.related_manager_cls(
            field=self.field,
            model=self.field.model,
            instance=instance,
            through=self.field.rels.through,
            query_field_name=field_names['src'],
            field_names=field_names,
            prefetch_cache_name=self.field.name,
        )

    def __set__(self, instance, value):
        manager = self.__get__(instance)
        # clear() can change expected output of 'value' queryset,
        # we force evaluation of queryset before clear; ticket #19816
        value = tuple(value)
        manager.clear()
        manager.add(*value)
