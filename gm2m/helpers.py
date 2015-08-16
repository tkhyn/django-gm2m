from django.contrib.contenttypes.models import ContentType

from .compat import is_fake_model, ModelState


def get_content_type(obj):

    klass = obj.__class__
    try:
        # obj is a model instance, retrieve database
        db = obj._state.db
    except AttributeError:
        # obj is a model class
        db = None

    if is_fake_model(klass):
        # if obj is an instance of a fake model for migrations purposes, use
        # ContentType's ModelState rather than ContentType itself (issue #14)
        # this should not raise LookupError as at this stage contenttypes must
        # be loaded
        ct_mngr = obj._meta.apps.get_model('contenttypes', 'ContentType') \
                                .objects.db_manager(db)
        # we erase the app cache to make sure a modelstate is returned when
        # calling get_for_model on the manager
        try:
            del ct_mngr.__class__._cache[db][(klass._meta.app_label,
                                              klass._meta.model_name)]
        except KeyError:
            pass
    else:
        ct_mngr = ContentType.objects.db_manager(db)

    return ct_mngr.get_for_model(obj)
