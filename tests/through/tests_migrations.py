from .. import base


class ThroughMultiMigrationTests(base.MultiMigrationsTestCase):

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
