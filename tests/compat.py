import django

__test__ = False

try:
    from unittest import mock
except ImportError:
    # Python 2
    import mock

try:
    from unittest2 import skipIf, skip  # python 2.6
except ImportError:
    from unittest import skipIf, skip

try:
    # Django 1.7+ apps registry
    from django.apps.registry import apps
    cache_models = apps.all_models
except ImportError:
    from django.db.models.loading import cache as apps
    apps.app_configs = True
    apps.set_installed_apps = lambda installed: None
    apps.unset_installed_apps = lambda: None
    cache_models = apps.app_models
