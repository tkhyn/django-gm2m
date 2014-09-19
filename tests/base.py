"""
Implements the base class for tests

All tests in tests.*.tests must derive from TestCase below
It takes care of resetting the models and databases for each Testcase
"""

import sys
from imp import reload
from importlib import import_module

from django import test
from django.conf import settings
from django.db.models.loading import cache
from django.utils.datastructures import SortedDict
from django.core.management import call_command
from django.utils import six
from django.db.models.fields import related
from django.contrib.contenttypes.models import ContentType

from .helpers import del_app_models


# no nose tests here !
__test__ = False
__unittest = True

NO_SETTING = ('!', None)


class TestSettingsManager(object):
    """
    A class which can modify some Django settings temporarily for a
    test and then revert them to their original values later.

    Automatically handles resyncing the DB if INSTALLED_APPS is
    modified.
    """

    def __init__(self):
        self._original_settings = {}

    def set(self, **kwargs):
        for k, v in six.iteritems(kwargs):
            self._original_settings.setdefault(k, getattr(settings,
                                                          k, NO_SETTING))
            setattr(settings, k, v)
        if 'INSTALLED_APPS' in kwargs:
            try:
                # django 1.7 apps registry
                from django.apps.registry import apps
                apps.set_installed_apps(kwargs['INSTALLED_APPS'])
            except ImportError:
                pass

            self.syncdb()

    def syncdb(self):
        cache.loaded = False
        cache.app_labels = {}
        cache.app_store = SortedDict()
        cache.handled = set()
        cache.postponed = []
        cache.nesting_level = 0
        cache._get_models_cache = {}
        cache.available_apps = None

        call_command('syncdb', verbosity=0)

    def revert(self):
        for k, v in six.iteritems(self._original_settings):
            if v == NO_SETTING:
                delattr(settings, k)
            else:
                setattr(settings, k, v)

        if 'INSTALLED_APPS' in self._original_settings:
            try:
                # django 1.7 apps registry
                from django.apps.registry import apps
                apps.unset_installed_apps()
            except ImportError:
                pass

            self.syncdb()

        self._original_settings = {}


class TestCase(test.TestCase):
    """
    A subclass of the Django TestCase with a settings_manager
    attribute which is an instance of TestSettingsManager.

    Comes with a tearDown() method that calls
    self.settings_manager.revert().
    """

    @classmethod
    def setUpClass(cls):

        cls.settings_manager = TestSettingsManager()

        # unloads the test.models module and test app to 'forget' the links
        # created by the previous test case
        del_app_models('tests')

        # resets ContentType's related object cache to 'forget' the links
        # created by the previous test case, they'll be regenerated
        try:
            del ContentType._meta._related_objects_cache
        except AttributeError:
            pass

        # finally, we need to reload the current test module as it relies upon
        # the app's models
        app_name = '.'.join(cls.__module__.split('.')[:2])
        del_app_models(app_name)  # to make sure the app models are flushed
        import_module(app_name)  # needed to be able to reload app.tests
        reload(sys.modules[cls.__module__])

        cls.settings_manager.set(
            INSTALLED_APPS=settings.INSTALLED_APPS + (app_name,))

    @classmethod
    def tearDownClass(cls):
        cls.settings_manager.revert()
        related.pending_lookups = {}

        del_app_models('.'.join(cls.__module__.split('.')[:2]),
                       app_module=True)
