from django.apps import AppConfig
from django.core import serializers


class GM2MConfig(AppConfig):
    name = 'gm2m'
    verbose_name = 'Django generic many-to-many field'

    def ready(self):

        from . import signals
        from . import monkeypatch

        serializers.BUILTIN_SERIALIZERS = {
            "xml": "gm2m.serializers.xml_serializer",
            "python": "gm2m.serializers.python",
            "json": "gm2m.serializers.json",
            "yaml": "gm2m.serializers.pyyaml",
        }
