from .. import base


class MigrationTests(base.MigrationsTestCase):

    def test_migrate_app(self):
        # just check that no exception is raised when calling migrate
        self.migrate()
