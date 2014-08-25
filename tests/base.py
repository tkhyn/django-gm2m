import sys
import inspect

from django import test
from django.conf import settings
from django.db import models
from django.utils.datastructures import SortedDict
from django.core.management import call_command
from django.utils import six
from django.db.models.fields import related

from gm2m.descriptors import GM2MRelatedDescriptor, \
                             ReverseGM2MRelatedDescriptor

from . import models as test_models

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

            # cleanup app models cache
            changed_apps = set(kwargs['INSTALLED_APPS']).difference(
                               self._original_settings['INSTALLED_APPS'])
            for app in changed_apps:
                app = app.split('.')[-1]
                if app in models.loading.cache.app_models:
                    del(models.loading.cache.app_models[app])

            self.syncdb()

            for app in changed_apps:
                models.loading.cache.register_models(app)

    def syncdb(self):
        cache = models.loading.cache
        cache.loaded = False
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
        global test_models
        module = cls.__module__
        app_module = module[:module.rfind('.')]
        cls.settings_manager = TestSettingsManager()
        test_models = reload(test_models)
        if app_module + '.models' in sys.modules:
            # if that's the 2nd class of the module, the models module should
            # be reloaded during syncdb
            del(sys.modules[app_module + '.models'])

        cls.settings_manager.set(
            INSTALLED_APPS=settings.INSTALLED_APPS + (app_module,))

        # reload the model classes in the test module, if any, so that the
        # instances in the test are created using the updated classes
        for m in dir(sys.modules[module]):
            modcls = getattr(sys.modules[module], m)
            if inspect.isclass(modcls) and issubclass(modcls, models.Model) \
            and not modcls._meta.abstract:
                setattr(sys.modules[module], m,
                        getattr(sys.modules[modcls.__module__],
                                modcls.__name__))

    @classmethod
    def tearDownClass(cls):
        cls.settings_manager.revert()
        related.pending_lookups = {}
