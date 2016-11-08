import os
from shutil import copy

from .. import base


class GM2MFieldAdditionTests(base.MultiMigrationsTestCase):

    def test_add_gm2mfield_and_migrate(self):
        # generates initial migration file 0001_initial
        self.makemigrations()
        self.migrate()

        # removes comment on GM2M line
        self.replace('# mig1: ', '')
        self.makemigrations()

        # check that no exception is raised when calling migrate
        self.migrate()

    def test_add_and_modify_gm2m_field(self):
        # generates initial migration file 0001_initial
        self.makemigrations()
        self.migrate()

        # removes comment on GM2M line
        self.replace('# mig1: ', '')
        self.makemigrations()
        self.migrate()

        # this restores the models.py file
        os.remove(self.models_path)
        copy(self.backup_path, self.models_path)

        self.replace('# mig2: ', '')
        self.makemigrations()
        # this is where it failed with django 1.10
        self.migrate()
