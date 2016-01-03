import os
import re

from .. import base


# basic migration tests
class MigrationTests(base.MigrationsTestCase):

    def test_makemigrations(self):
        self.makemigrations()

        mig_ctnt = re.sub(r'models\.AutoField\(.+?\)', 'models.AutoField()',
                          self.get_migration_content())
        mig_ctnt = re.sub(r"([\s\(])b'", r"\1'", mig_ctnt)

        self.assertIn("""
    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Links',
            fields=[
                ('id', models.AutoField()),
                ('related_objects', gm2m.fields.GM2MField(through_fields=('gm2m_src', 'gm2m_tgt', 'gm2m_ct', 'gm2m_pk'))),
            ],
        ),
    ]""", mig_ctnt)

    def test_migrate_app(self):
        # just check that no exception is raised when calling migrate after
        # makemigrations
        self.makemigrations()
        self.migrate()

    def test_migrate_all(self):
        self.migrate(all=True)


class MultiMigrationTests(base.MultiMigrationsTestCase):

    def test_migrate_app(self):
        # generates initial migration file 0001_initial
        self.makemigrations()

        # adds a pk_maxlength parameter and generate 2nd migration
        self.replace('gm2m.GM2MField()',
                     'gm2m.GM2MField(pk_maxlength=50)')
        self.makemigrations()

        # renames the GM2MField
        self.replace('related_objects', 'projects_and_tasks')
        self.makemigrations()

        # check that no exception is raised when calling migrate
        self.migrate()

    def test_add_gm2m_in_runpython(self):
        """
        Bug #14
        """

        self.makemigrations()
        self.migrate()

        self.models.Links.objects.create()
        self.models.Project.objects.create()

        mig2 = open(os.path.join(os.path.dirname(__file__), 'migrations',
                                 '0002_runpython.py'), 'w')

        mig2.write("""
from django.db import migrations


def add_gm2m(apps, schema_editor):
    links_model = apps.get_model('norevrel', 'Links')
    project_model = apps.get_model('app', 'Project')

    links_model.objects.first().related_objects.add(
        project_model.objects.first())


class Migration(migrations.Migration):
    dependencies = [
        ('norevrel', '0001_initial'),
    ]
    operations = [
        migrations.RunPython(add_gm2m),
    ]
""")
        mig2.close()

        self.migrate()
