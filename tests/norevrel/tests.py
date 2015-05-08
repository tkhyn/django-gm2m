import re

import django

from .. import base


class NoRevRelTests(base.TestCase):

    def setUp(self):
        self.project = self.models.Project.objects.create()
        self.task1 = self.models.Task.objects.create()
        self.task2 = self.models.Task.objects.create()
        self.links = self.models.Links.objects.create()


class OperationsTests(NoRevRelTests):

    def test_add(self):
        self.links.related_objects.add(self.project)
        self.assertIn(self.project, self.links.related_objects.all())

    def test_set(self):
        self.links.related_objects = [self.project]
        self.assertEqual(self.links.related_objects.count(), 1)
        self.assertEqual(self.links.related_objects.all()[0], self.project)

    def test_remove(self):
        self.links.related_objects = [self.project, self.task1]
        self.links.related_objects.remove(self.project)
        self.assertEqual(self.links.related_objects.count(), 1)
        self.assertEqual(self.links.related_objects.all()[0], self.task1)

    def test_clear(self):
        self.links.related_objects = [self.project, self.task1]
        self.assertEqual(self.links.related_objects.count(), 2)
        self.links.related_objects.clear()
        self.assertEqual(self.links.related_objects.count(), 0)


class AutoReverseTests(NoRevRelTests):

    def test_auto_reverse_accessors(self):
        with self.assertRaises(AttributeError):
            self.assertEqual(self.project.links_set.count(), 0)
        self.links.related_objects = [self.project, self.task1]
        self.assertListEqual(list(self.project.links_set.all()), [self.links])
        self.assertListEqual(list(self.task1.links_set.all()), [self.links])


class MigrationTests(base.MigrateTestCase):

    def test_makemigrations(self):
        self.makemigrations()

        mig_ctnt = re.sub('models\.AutoField\(.+?\)', 'models.AutoField()',
                          self.get_migration_content())

        if django.VERSION >= (1, 8):
            self.assertIn("""
    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Links',
            fields=[
                ('id', models.AutoField()),
                ('related_objects', gm2m.fields.GM2MField()),
            ],
        ),
    ]""", mig_ctnt)

        else:
            # django < 1.7
            self.assertIn("""
    dependencies = [
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Links',
            fields=[
                ('id', models.AutoField()),
                ('related_objects', gm2m.fields.GM2MField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]""", mig_ctnt)

    def test_migrate_app(self):
        # just check that no exception is raised when calling migrate
        self.makemigrations()
        self.migrate()

    def test_migrate_all(self):
        self.migrate(all=True)
