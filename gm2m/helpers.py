from django.db.models import Manager
from django.db.migrations.state import StateApps
from django.utils.functional import cached_property
from django.utils import six

from .contenttypes import ct


def is_fake_model(model):
    """
    Is ``model`` a 'state' model (generated for migrations)
    """
    return isinstance(model._meta.apps, StateApps)


class GM2MTo(object):
    """
    A 'dummy' model-like class that enables django to find out that GM2MField
    depends on contenttypes, and provides a specific manager for deserialization
    (amongst other things)

    Indeed, unlike a GFK, GM2MField does not create any FK to ContentType on
    the source model
    """

    def __init__(self):
        self._meta = GM2MToOptions()
        self._default_manager = GM2MToManager()


class GM2MToOptions(object):

    def __init__(self):
        self.object_name = 'ContentType'
        self.model_name = 'contenttype'
        self.app_label = 'contenttypes'

    def __str__(self):
        return 'gm2m.to'

    @cached_property
    def concrete_model(self):
        return ct.ContentType


class GM2MToManager(Manager):

    def get_by_natural_key(self, ct_key, key):
        """
        Used for deserialization (this is actually a workaround to avoid
        heavy monkey-patching)
        :param ct_key: the content type's natural key
        :param key: the object key (may be a natural key)
        :return:
        """

        model = ct.ContentType.objects.get_by_natural_key(*ct_key).model_class()
        mngr = model._default_manager.db_manager(self.db)

        if hasattr(model._default_manager, 'get_by_natural_key'):
            if hasattr(key, '__iter__') and not isinstance(key, six.text_type):
                obj = mngr.get_by_natural_key(*key)
            else:
                obj = mngr.get_by_natural_key(key)
        else:
            obj = mngr.get(pk=key)

        # django's Deserializer only cares about the pk attribute, but we
        # need the actual instance
        gm2mto = GM2MTo()
        gm2mto.pk = obj

        return gm2mto
