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

        # add atomic = False to last migration, otherwise it raises an error
        # with sqlite
        for mig_name in os.listdir(self.migrations_dir):
            if mig_name.startswith('0003'):
                break
        mig_path = os.path.join(self.migrations_dir, mig_name)
        with open(mig_path, 'rt') as fh:
            code = fh.read()
        with open(mig_path, 'w') as fh:
            fh.write(code.replace('    dependencies',
                                  '    atomic = False\n\n    dependencies'))
        self.invalidate_caches()

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

def rem_gm2m(apps, schema_editor):
    links_model = apps.get_model('norevrel', 'Links')
    project_model = apps.get_model('app', 'Project')

    links_model.objects.first().related_objects.remove(
        project_model.objects.first())

class Migration(migrations.Migration):
    dependencies = [
        ('norevrel', '0001_initial'),
    ]
    operations = [
        migrations.RunPython(add_gm2m, rem_gm2m),
    ]
""")
        mig2.close()

        self.migrate()

    def test_rename_model(self):
        """
        Issue #37
        We have to create a custom migration as the auto created one deletes and
        recreates the model
        """

        # create initial migration
        self.makemigrations()

        mig2 = open(os.path.join(os.path.dirname(__file__), 'migrations',
                                 '0002_rename_model.py'), 'w')

        mig2.write("""
from django.db import migrations


class Migration(migrations.Migration):
    atomic = False
    dependencies = [
        ('norevrel', '0001_initial'),
    ]
    operations = [
        migrations.RenameModel('Links', 'LinksRenamed'),
    ]
""")
        mig2.close()

        self.replace('Links', 'LinksRenamed')

        self.migrate()
