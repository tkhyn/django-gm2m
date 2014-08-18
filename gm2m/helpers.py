from django.contrib.contenttypes.models import ContentType


def get_content_type(obj):
    return ContentType.objects.db_manager(obj._state.db).get_for_model(obj)
