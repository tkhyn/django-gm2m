from django import test
from django.conf import settings
from django.db.models import loading
from django.utils.datastructures import SortedDict
from django.core.management import call_command
from django.utils import six

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
        loading.cache.loaded = False
        loading.cache.app_store = SortedDict()
        loading.cache.handled = set()
        loading.cache.postponed = []
        loading.cache.nesting_level = 0
        loading.cache._get_models_cache = {}
        loading.cache.available_apps = None

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
        module = cls.__module__
        app = module[:module.rfind('.')]
        cls.settings_manager = TestSettingsManager()
        cls.settings_manager.set(
            INSTALLED_APPS=settings.INSTALLED_APPS + (app,))

    @classmethod
    def tearDownClass(cls):
        cls.settings_manager.revert()
