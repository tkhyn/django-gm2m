from django.contrib.contenttypes.models import ContentType

from .compat import is_fake_model, ModelState


def get_content_type(obj):

    klass = obj.__class__
    ct_class = ContentType
    if is_fake_model(klass):
        # if obj is an instance of a fake model for migrations purposes, use
        # ContentType's ModelState rather than ContentType itself (issue #14)
        # this should not raise LookupError as at this stage contenttypes must
        # be loaded
        ct_class = obj._meta.apps.get_model('contenttypes', 'ContentType')

    ct_mngr = ct_class.objects
    try:
        # obj is a model instance, retrieve database
        qs = ct_mngr.db_manager(obj._state.db)
    except AttributeError:
        # obj is a model class
        qs = ct_mngr

    return qs.get_for_model(obj)
