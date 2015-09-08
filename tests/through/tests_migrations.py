import django

from .. import base


class ThroughMultiMigrationTests(base.MultiMigrationsTestCase):

    @base.skipIf(django.VERSION < (1, 8),
                 'Bug in model renaming in migrations in django 1.7. '
                 'See https://code.djangoproject.com/ticket/22931')
    def test_migrate_app(self):
        # generates initial migration file 0001_initial
        self.makemigrations()

        # renames 'target*' fields in 'tgt*'
        self.replace('target', 'tgt')
        self.makemigrations()

        # renames the through model
        self.replace('RelLinks', 'ThroughLinks')
        self.makemigrations()

        # check that no exception is raised when calling migrate
        self.migrate()
