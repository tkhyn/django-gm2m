from django.utils.functional import cached_property


class _CTClasses(object):

    @cached_property
    def ContentType(self):
        from django.contrib.contenttypes.models import ContentType
        return ContentType

    @cached_property
    def ContentTypeManager(self):
        from django.contrib.contenttypes.models import ContentTypeManager
        return ContentTypeManager

    @cached_property
    def GenericForeignKey(self):
        from django.contrib.contenttypes.fields import GenericForeignKey
        return GenericForeignKey


ct = _CTClasses()
