from django.apps import AppConfig


class GM2MConfig(AppConfig):
    name = 'gm2m'
    verbose_name = 'Django generic many-to-many field'

    def ready(self):

        from . import signals
        from . import monkeypatch
