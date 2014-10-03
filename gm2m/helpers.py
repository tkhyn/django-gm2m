from django.contrib.contenttypes.models import ContentType


def get_content_type(obj):
    ct_mngr = ContentType.objects
    try:
        # obj is a model instance, retrieve database
        qs = ct_mngr.db_manager(obj._state.db)
    except AttributeError:
        # obj is a model class
        qs = ct_mngr
    return qs.get_for_model(obj)
