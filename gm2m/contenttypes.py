from django.utils.functional import cached_property


class _CTModels(object):

    @cached_property
    def ContentType(self):
        from django.contrib.contenttypes.models import ContentType
        return ContentType

    @cached_property
    def ContentTypeManager(self):
        from django.contrib.contenttypes.models import ContentTypeManager
        return ContentTypeManager


class _CTFields(object):

    @cached_property
    def GenericForeignKey(self):
        from django.contrib.contenttypes.fields import GenericForeignKey
        return GenericForeignKey


models = _CTModels()
fields = _CTFields()
