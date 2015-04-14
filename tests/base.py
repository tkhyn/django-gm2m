"""
Implements the base class for tests

All tests in tests.*.tests must derive from TestCase below
It takes care of resetting the models and databases for each Testcase
"""

import sys
from imp import reload
from importlib import import_module


import django
from django import test
from django.conf import settings
from django.utils.datastructures import SortedDict
from django.core.management import call_command
from django.utils import six
from django.db.models.fields import related
from django.contrib.contenttypes.models import ContentType

from gm2m import GM2MField

from .compat import apps, cache_handled_init, skip, skipIf
from .helpers import app_mod_path, del_app_models


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
        if not apps.app_configs:
            apps.populate(settings.INSTALLED_APPS)

        for k, v in six.iteritems(kwargs):
            self._original_settings.setdefault(k, getattr(settings,
                                                          k, NO_SETTING))
            setattr(settings, k, v)

        if 'INSTALLED_APPS' in kwargs:
            apps.set_installed_apps(kwargs['INSTALLED_APPS'])
            self.syncdb()

    def syncdb(self):
        apps.loaded = False
        apps.app_labels = {}
        apps.app_store = SortedDict()
        apps.handled = cache_handled_init()
        apps.postponed = []
        apps.nesting_level = 0
        apps._get_models_cache = {}
        apps.available_apps = None

        call_command('syncdb', verbosity=0, interactive=False)

    def revert(self):
        for k, v in six.iteritems(self._original_settings):
            if v == NO_SETTING:
                delattr(settings, k)
            else:
                setattr(settings, k, v)

        if 'INSTALLED_APPS' in self._original_settings:
            apps.unset_installed_apps()
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
        del_app_models('app')

        # resets ContentType's related object cache to 'forget' the links
        # created by the previous test case, they'll be regenerated
        try:
            del ContentType._meta._related_objects_cache
        except AttributeError:
            pass

        # finally, we need to reload the current test module as it relies upon
        # the app's models
        app_name = cls.__module__.split('.')[1]
        app_path = app_mod_path(app_name)
        del_app_models(app_name)  # to make sure the app models are flushed
        import_module(app_path)  # needed to import app.test
        reload(sys.modules[cls.__module__])

        cls.settings_manager.set(
            INSTALLED_APPS=settings.INSTALLED_APPS + (app_path,))

    @classmethod
    def tearDownClass(cls):
        cls.settings_manager.revert()
        related.pending_lookups = {}

        del_app_models(cls.__module__.split('.')[1], app_module=True)

    @skipIf(django.VERSION < (1, 7),
            'deconstruct method does not exist for django < 1.7')
    def test_deconstruct(self):
        # this test will run on *all* testcases having no subclasses

        if self.__class__.__subclasses__():
            return skip('not an end test class')

        try:
            field = self.links.__class__._meta.get_field('related_objects')
        except AttributeError:
            return

        __, __, args, kwargs = field.deconstruct()
        new_field = GM2MField(*args, **kwargs)

        for attr in (''):
            self.assertEqual(getattr(field, attr),
                             getattr(new_field, attr))

        for attr in (''):
            self.assertEqual(getattr(field.rel, attr),
                             getattr(new_field.rel, attr))

        # just checking the stings output, as for an attr to attr comparison
        # we would need to run contribute_to_class
        self.assertSetEqual(set(['%s.%s' % (r.to._meta.app_label,
                                            r.to._meta.object_name)
                                 for r in field.rel.rels
                                 if not getattr(r, '_added', False)]),
                            set(args))
