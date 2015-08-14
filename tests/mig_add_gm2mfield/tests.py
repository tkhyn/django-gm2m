from .. import base


class GM2MFieldAdditionTests(base.MultiMigrationsTestCase):

    def test_add_gm2mfield_and_migrate(self):
        # generates initial migration file 0001_initial
        self.makemigrations()
        self.migrate()

        # removes comment on GM2M line
        self.replace('# ', '')
        self.makemigrations()

        # check that no exception is raised when calling migrate
        self.migrate()
