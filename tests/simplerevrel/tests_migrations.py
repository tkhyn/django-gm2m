import os

from .. import base


class SimpleRevRelMigrationTests(base.MultiMigrationsTestCase):

    def test_reverse_manager_in_runpython(self):
        """
        Bug #14
        """

        self.makemigrations()
        self.migrate()

        l = self.models.Links.objects.create()
        p = self.models.Project.objects.create()
        l.related_objects.add(p)

        mig2 = open(os.path.join(os.path.dirname(__file__), 'migrations',
                                 '0002_runpython.py'), 'w')

        mig2.write("""
from django.db import migrations


def call_rev_mngr(apps, schema_editor):
    links_model = apps.get_model('simplerevrel', 'Links')
    project_model = apps.get_model('app', 'Project')

    for l in project_model.objects.first().links_set.all():
        continue

class Migration(migrations.Migration):
    dependencies = [
        ('simplerevrel', '0001_initial'),
    ]
    operations = [
        migrations.RunPython(call_rev_mngr),
    ]
""")
        mig2.close()

        self.migrate()
