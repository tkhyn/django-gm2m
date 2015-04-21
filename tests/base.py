"""
Implements the base class for tests

All tests in tests.*.tests must derive from TestCase below
It takes care of resetting the models and databases for each Testcase
"""

import sys
import os
from imp import reload
from importlib import import_module
from inspect import getfile
from shutil import rmtree

import django
from django import test
from django.conf import settings
from django.utils.datastructures import SortedDict
from django.core.management import call_command
from django.utils import six
from django.db import models, connection
from django.db.models.fields import related
from django.contrib.contenttypes.models import ContentType
from django.utils.six import StringIO

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


class Models(object):
    pass


class _TestCase(test.TestCase):
    """
    A subclass of the Django TestCase with a settings_manager
    attribute which is an instance of TestSettingsManager.

    Comes with a tearDown() method that calls
    self.settings_manager.revert().
    """

    other_apps = ()

    @classmethod
    def app_name(cls):
        return cls.__module__.split('.')[1]

    @classmethod
    def setUpClass(cls):

        cls.settings_manager = TestSettingsManager()

        cls.inst_apps = ('app', cls.app_name(),) + cls.other_apps

        # unloads the test.models module and test app to make sure no link
        # subsists from the previous test case
        for app in cls.inst_apps:
            del_app_models(app, app_module=True)

        # resets ContentType's related object cache to 'forget' the links
        # created by the previous test case, they'll be regenerated
        try:
            del ContentType._meta._related_objects_cache
        except AttributeError:
            pass

        # finally, we need to reload the current test module as it relies upon
        # the app's models
        # needed to import app.test
        app_paths = tuple([app_mod_path(app) for app in cls.inst_apps])
        import_module(app_mod_path(cls.inst_apps[1]))
        reload(sys.modules[cls.__module__])

        cls.settings_manager.set(INSTALLED_APPS=settings.INSTALLED_APPS
                                 + app_paths)

        # import the needed models
        cls.models = Models()
        for app_path in app_paths:
            module = import_module(app_path + '.models')
            for mod_name in dir(module):
                model = getattr(module, mod_name)
                if isinstance(model, models.base.ModelBase) \
                and not model._meta.abstract:
                    setattr(cls.models, mod_name, model)

    @classmethod
    def tearDownClass(cls):
        cls.settings_manager.revert()
        related.pending_lookups = {}

        cls.models = Models()
        for app in cls.inst_apps:
            del_app_models(app, app_module=True)


class TestCase(_TestCase):

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


@skipIf(django.VERSION < (1, 7), 'no migrations in django < 1.7')
class MigrationsTestCase(_TestCase):

    def _post_teardown(self):
        try:
            mig_dir = self.migrations_dir
            for d in (mig_dir, mig_dir + '_bak'):
                try:
                    rmtree(d)
                except OSError:
                    pass
        finally:
            try:
                del sys.modules[self.migrations_module]
            except KeyError:
                pass
            finally:
                super(MigrationsTestCase, self)._post_teardown()

    def makemigrations(self):
        call_command('makemigrations', self.app_name())

    def migrate(self, all=False):
        app_name = self.app_name()

        # drop the application's tables
        # we need to 'hide' the migrations module from django to generate the
        # sql
        mig_dir = self.migrations_dir
        sql_io = StringIO()
        try:
            os.rename(mig_dir, mig_dir + '_bak')
            do_rename = True
        except OSError:
            do_rename = False
        try:
            del sys.modules[self.migrations_module]
        except KeyError:
            pass
        call_command('sqlclear', app_name, stdout=sql_io)
        if do_rename:
            os.rename(mig_dir + '_bak', mig_dir)

        sql_io.seek(0)
        sql = sql_io.read()
        for statement in sql.split('\n')[1:-3]:
            connection.cursor().execute(statement)

        # migrate
        if all:
            args = []
        else:
            args = [app_name]
        call_command('migrate', *args)

    @property
    def migrations_dir(self):
        return os.path.join(os.path.dirname(getfile(self.__class__)),
                            'migrations')

    @property
    def migrations_module(self):
        return '.'.join(self.__class__.__module__.split('.')[:-1]
                        + ['migrations'])

    def get_migration_content(self, module='0001_initial'):
        f = open(os.path.join(self.migrations_dir, module + '.py'))
        s = f.read()
        f.close()
        return s
