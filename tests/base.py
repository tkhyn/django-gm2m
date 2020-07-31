"""
Implements the base class for tests

All tests in tests.*.tests must derive from TestCase below
It takes care of resetting the models and databases for each Testcase
"""

import sys
import os
from imp import reload
import importlib
from inspect import getfile
from shutil import rmtree, copy
import warnings
from unittest import skip

from django import test
from django.conf import settings
from django.core.management import call_command
from django.db import models
from django.db.models.fields import related
from django.apps.registry import apps
from django.utils.deprecation import RemovedInNextVersionWarning

from gm2m import GM2MField
from gm2m.contenttypes import ct

from .helpers import app_mod_path, del_app_models, reset_warning_registry


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

        for k, v in kwargs.items():
            self._original_settings.setdefault(k, getattr(settings,
                                                          k, NO_SETTING))
            setattr(settings, k, v)

        if 'INSTALLED_APPS' in kwargs:
            apps.set_installed_apps(kwargs['INSTALLED_APPS'])
            if kwargs.get('migrate', True):
                self.migrate()

    def migrate(self):
        for dicname in ('app_labels', 'app_store', 'handled',
                        '_get_models_cache'):
            getattr(apps, dicname, {}).clear()

        apps.loaded = False
        apps.postponed = []
        apps.nesting_level = 0
        apps.available_apps = None

        call_command('migrate', run_syncdb=True,
                     verbosity=0, interactive=False)

    def revert(self, migrate=True):
        for k, v in self._original_settings.items():
            if v == NO_SETTING:
                delattr(settings, k)
            else:
                setattr(settings, k, v)

        if 'INSTALLED_APPS' in self._original_settings:
            apps.unset_installed_apps()
            if migrate:
                self.migrate()

        self._original_settings = {}


class Models(object):
    pass


class _TestCase(object):
    """
    A mixin for Django (Transaction)TestCase subclasses, with a settings_manager
    attribute which is an instance of TestSettingsManager.

    Comes with a tearDown() method that calls
    self.settings_manager.revert().
    """

    inst_apps = ()
    other_apps = ()
    settings_manager = None

    @classmethod
    def app_name(cls):
        return cls.__module__.split('.')[1]

    @classmethod
    def invalidate_caches(cls):
        """
        Invalidate import finders caches
        https://docs.python.org/3/library/importlib.html#importlib.invalidate_caches
        """
        try:
            # python 3
            importlib.invalidate_caches()
        except AttributeError:
            pass

    @classmethod
    def setUpClass(cls):

        cls.settings_manager = TestSettingsManager()

        cls.inst_apps = ('app', cls.app_name(),) + cls.other_apps

        # unloads the test.models module and test app to make sure no link
        # subsists from the previous test case
        for app in cls.inst_apps:
            del_app_models(app, app_module=True)

        cls.invalidate_caches()

        # we also need to reload the current test module as it relies upon the
        # app's models needed to import app.test
        app_paths = tuple([app_mod_path(app) for app in cls.inst_apps])
        importlib.import_module(app_mod_path(cls.inst_apps[1]))
        reload(sys.modules[cls.__module__])

        cls.settings_manager.set(INSTALLED_APPS=settings.INSTALLED_APPS
                                 + app_paths)

        # import the needed models
        cls.models = Models()
        for app_path in app_paths:
            m = importlib.import_module(app_path + '.models')
            for mod_name in dir(m):
                model = getattr(m, mod_name)
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

    def run(self, result=None):
        with reset_warning_registry():
            return super(_TestCase, self).run(result)


class TestCase(_TestCase, test.TestCase):

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

        # just checking the strings output, as for an attr to attr comparison
        # we would need to run contribute_to_class
        self.assertSetEqual(set(['%s.%s' % (r.model._meta.app_label,
                                            r.model._meta.object_name)
                                 for r in field.remote_field.rels
                                 if not getattr(r, '_added', False)]),
                            set(args))

    def test_check(self):
        with warnings.catch_warnings():
            warnings.filterwarnings('error',
                                    category=RemovedInNextVersionWarning)
            call_command('check')


class MigrationsTestCase(_TestCase, test.TransactionTestCase):
    """
    Handles migration module deletion after they are generated
    """

    @classmethod
    def setUpClass(cls):
        super(MigrationsTestCase, cls).setUpClass()
        cls.migrations_dir = os.path.join(os.path.dirname(getfile(cls)),
                                          'migrations')
        cls.migrations_module = '.'.join(cls.__module__.split('.')[:-1]
                                         + ['migrations'])

    def _post_teardown(self):
        # revert migrations, if any
        if os.path.exists(self.migrations_dir):
            self.migrate(to='0001_initial')

        ct.ContentType.objects.clear_cache()

        mig_modules = [self.migrations_module]
        mig_dir = self.migrations_dir

        try:
            try:
                mig_modules += [
                    self.migrations_module + '.' + os.path.splitext(m)[0]
                    for m in os.listdir(mig_dir) if m != '__init__.py'
                ]
            except OSError:
                pass

            for m in mig_modules:
                try:
                    del sys.modules[m]
                except KeyError:
                    pass

            for d in (mig_dir, mig_dir + '_bak'):
                try:
                    rmtree(d)
                except OSError:
                    pass
        finally:
            super(MigrationsTestCase, self)._post_teardown()

    def get_migration_content(self, module='0001_initial'):
        f = open(os.path.join(self.migrations_dir, module + '.py'))
        s = f.read()
        f.close()
        return s

    def makemigrations(self):
        call_command('makemigrations', self.app_name())
        # new modules have been created, sys.meta_path caches must be cleared
        self.invalidate_caches()

    def migrate(self, all=False, to=None):
        app_name = self.app_name()
        if all:
            args = []
        else:
            args = [app_name]
            if to is not None:
                args.append(to)

        # we need to use fake_initial as the database has already been
        # initialized and is in the state of the initial migration
        call_command('migrate', *args, verbosity=0, interactive=False,
                     fake_initial=True)


class MultiMigrationsTestCase(MigrationsTestCase):
    """
    The models module can be modified to generate several migrations
    """

    @classmethod
    def setUpClass(cls):
        super(MultiMigrationsTestCase, cls).setUpClass()
        directory = os.path.dirname(getfile(cls))
        cls.models_path = os.path.join(directory, 'models.py')
        cls.backup_path = os.path.join(directory, 'models.py.bak')
        try:
            os.remove(cls.backup_path)
        except OSError:
            pass

    def _pre_setup(self):
        # creates a backup copy of the models module
        os.rename(self.models_path, self.backup_path)
        copy(self.backup_path, self.models_path)
        super(MultiMigrationsTestCase, self)._pre_setup()

    def _post_teardown(self):
        super(MultiMigrationsTestCase, self)._post_teardown()
        # restores the backup copy
        os.remove(self.models_path)
        os.rename(self.backup_path, self.models_path)
        # reloading all apps as models have been changed a final time
        self.reload_apps()

    def replace(self, old_str, new_str):
        """
        Carries out a search and replace on the models module
        """
        with open(self.models_path, 'rt') as fh:
            code = fh.read()
        with open(self.models_path, 'w') as fh:
            fh.write(code.replace(old_str, new_str))
        self.reload_apps()

    def reload_apps(self):
        # reload apps so that next migration can be generated (yes, all of
        # them, it does not work if only the test one is reloaded)
        cls = self.__class__
        cls.settings_manager.revert(migrate=False)
        for app in cls.inst_apps:
            del_app_models(app, app_module=True)

        # this implies clearing the content types cache
        ct.ContentType.objects.clear_cache()

        app_paths = tuple([app_mod_path(app) for app in cls.inst_apps])
        cls.settings_manager.set(INSTALLED_APPS=settings.INSTALLED_APPS
                                 + app_paths, migrate=False)
