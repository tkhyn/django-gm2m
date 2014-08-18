from django.contrib.contenttypes.models import ContentType


def get_content_type(obj):
    return ContentType.objects.db_manager(obj._state.db).get_for_model(obj)


def get_model_name(cls):
    opts = cls._meta
    try:
        return opts.model_name
    except AttributeError:
        # Django < 1.6
        return opts.module_name.lower()
