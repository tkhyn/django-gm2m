import django
from django.db.models.loading import cache

try:
    from unittest import mock
except ImportError:
    # Python 2
    import mock

__test__ = False

try:
    # Django 1.7 apps registry
    from django.apps.registry import apps
except ImportError:
    # create a dummy apps object
    class DummyApps(object):
        app_configs = True

        def populate(self, *args, **kwargs):
            pass

        def set_installed_apps(self, *args, **kwargs):
            pass

        def unset_installed_apps(self, *args, **kwargs):
            pass

    apps = DummyApps()

try:  # Django >= 1.7
    cache_models = cache.all_models
except AttributeError:
    cache_models = cache.app_models


def cache_handled_init():
    return {} if django.VERSION < (1, 6) else set()
