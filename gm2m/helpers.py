from django.db import models
from django.db.migrations.state import StateApps
from django.utils.functional import cached_property
from django.utils import six

from .contenttypes import ct


def is_fake_model(model):
    """
    Is ``model`` a 'state' model (generated for migrations)
    """
    return isinstance(model._meta.apps, StateApps)


# Hereafter, the aim is to create a 'dummy' model class that:
#  - enables django to find out that GM2MField depends on contenttypes
#  - provides a specific manager for deserialization

# Indeed, unlike a GFK, GM2MField does not create any FK to ContentType on
# the source model, so we need to let django know about that


class GM2MModelOptions(object):

    def __init__(self):
        self.object_name = 'ContentType'
        self.model_name = 'contenttype'
        self.app_label = 'contenttypes'

        self.concrete_fields = []
        self.pk = None

    def __str__(self):
        return 'gm2m.model'

    @cached_property
    def concrete_model(self):
        return ct.ContentType


class GM2MModelManager(models.Manager):

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
        gm2mto = GM2MModel()
        gm2mto.pk = obj

        return gm2mto


class Dummy(object):
    """
    We can't derive our dummy model class from models.Model explicitly, as if we
    do it triggers all the django machinery through the metaclass. To prevent
    this, we derive from a Dummy class and then overwrite the __bases__ (as we
    are not allowed to replace __bases__ on a class tha derives from `object`
    """


class GM2MModel(Dummy):
    """
    We need to define pk as we're using that attribute in the GM2MToManager
    above
    """
    pk = None


GM2MModel.__bases__ = (models.Model,)
GM2MModel._meta = GM2MModelOptions()
GM2MModel._default_manager = GM2MModelManager()
