"""
Generic many-to-many relations descriptors
"""


class GM2MDescriptor(object):

    def __init__(self, field):
        self.field = field

    def __get__(self, instance, instance_type=None):
        if instance is None:
            return self
        return self.related_manager_cls(instance)

    def __set__(self, instance, value):
        if not self.through._meta.auto_created:
            opts = self.through._meta
            raise AttributeError(
                'Cannot set values on a GM2MField which specifies an '
                'intermediary model. Use %s.%s\'s Manager instead.'
                % (opts.app_label, opts.object_name))
        manager = self.__get__(instance)
        manager.set(value)


class GM2MRelatedDescriptor(GM2MDescriptor):
    """
    Provides a generic many-to-many descriptor to make the related manager
    available from the source model class
    """

    def __init__(self, related, rel):
        super(GM2MRelatedDescriptor, self).__init__(related)
        self.rel = rel

    @property
    def through(self):
        return self.rel.through

    @property
    def related_manager_cls(self):
        return self.rel.related_manager_cls


class ReverseGM2MRelatedDescriptor(GM2MDescriptor):
    """
    Provides a generic many-to-many descriptor to make the source manager
    available from a target model class
    """

    def add_relation(self, *args, **kwargs):
        return self.field.add_relation(*args, **kwargs)

    @property
    def through(self):
        return self.field.rel.through

    @property
    def related_manager_cls(self):
        return self.field.rel.related_manager_cls

    def __set__(self, instance, value):
        # clear() can change expected output of 'value' queryset,
        # we force evaluation of queryset before clear; django ticket #19816
        value = tuple(value)
        super(ReverseGM2MRelatedDescriptor, self).__set__(instance, value)
