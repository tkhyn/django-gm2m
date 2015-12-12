from .contenttypes import ct
from .compat import is_fake_model


def get_content_type(obj):

    try:
        # obj is a model instance, retrieve database
        db = obj._state.db
        klass = obj.__class__
    except AttributeError:
        # obj is a model class
        db = None
        klass = obj

    ct_mngr = ct.ContentTypeManager().db_manager(db)
    if is_fake_model(klass):
        # if obj is an instance of a fake model for migrations purposes, use
        # ContentType's ModelState rather than ContentType itself (issue #14)
        # this should not raise LookupError as at this stage contenttypes must
        # be loaded
        ct_mngr.model = obj._meta.apps.get_model('contenttypes', 'ContentType')
        # we erase the app cache to make sure a modelstate is returned when
        # calling get_for_model on the manager
        try:
            del ct_mngr.__class__._cache[db][(klass._meta.app_label,
                                              klass._meta.model_name)]
        except KeyError:
            pass
    else:
        ct_mngr.model = ct.ContentType

    return ct_mngr.get_for_model(obj)
