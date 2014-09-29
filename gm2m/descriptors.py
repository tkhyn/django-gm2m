from django.db.models.fields.related import ManyRelatedObjectsDescriptor, \
                                            ReverseManyRelatedObjectsDescriptor
from django.utils.functional import cached_property


from .managers import create_gm2m_related_manager
from .compat import get_model_name


class GM2MDescriptor(object):

    def __get__(self, instance, instance_type=None):
        if instance is None:
            return self
        return self.related_manager_cls(instance)

    def __set__(self, instance, value):
        manager = self.__get__(instance)
        manager.clear()
        manager.add(*value)


class GM2MRelatedDescriptor(GM2MDescriptor, ManyRelatedObjectsDescriptor):
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
            superclass=self.rel.to._default_manager.__class__,
            field=self.related.field,
            model=self.related.model,
            through=self.rel.through,
            query_field_name=get_model_name(self.related.field.rels.through),
            field_names=self.related.field.rels.through._meta._field_names,
            prefetch_cache_name=self.related.field.related_query_name()
        )

    def __set__(self, instance, value):
        if not self.related.field.rels.through._meta.auto_created:
            opts = self.related.field.rels.through._meta
            raise AttributeError(
                'Cannot set values on a ManyToManyField which specifies an '
                'intermediary model. Use %s.%s\'s Manager instead.'
                % (opts.app_label, opts.object_name))
        super(GM2MRelatedDescriptor, self).__set__(instance, value)


class ReverseGM2MRelatedDescriptor(GM2MDescriptor,
                                   ReverseManyRelatedObjectsDescriptor):
    """
    Provides a generic many-to-many descriptor to make the source manager
    available from a target model class
    """

    def add_relation(self, *args, **kwargs):
        return self.field.add_relation(*args, **kwargs)

    @cached_property
    def related_manager_cls(self):
        field_names = self.field.rels.through._meta._field_names
        return create_gm2m_related_manager(
            superclass=None,
            field=self.field,
            model=self.field.rels.through,
            through=self.field.rels.through,
            query_field_name=field_names['src'],
            field_names=field_names,
            prefetch_cache_name=self.field.name
        )

    def __set__(self, instance, value):
        if not self.field.rels.through._meta.auto_created:
            opts = self.field.rels.through._meta
            raise AttributeError(
                'Cannot set values on a ManyToManyField which specifies an '
                'intermediary model. Use %s.%s\'s Manager instead.'
                % (opts.app_label, opts.object_name))
        # clear() can change expected output of 'value' queryset,
        # we force evaluation of queryset before clear; django ticket #19816
        value = tuple(value)
        super(ReverseGM2MRelatedDescriptor, self).__set__(instance, value)
