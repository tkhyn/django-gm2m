from ..app.models import Project, Task
from .models import Links

from ..base import TestCase


class LinksTests(TestCase):

    def setUp(self):
        self.project = Project.objects.create()
        self.task1 = Task.objects.create()
        self.task2 = Task.objects.create()
        self.links = Links.objects.create()

    def test_add(self):
        self.links.related_objects.add(self.project)
        self.links.save()
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

    def test_reverse(self):
        self.links.related_objects = [self.project, self.task1]
        self.links.save()
        self.assertListEqual(list(self.project.links_set.all()), [self.links])
        self.assertListEqual(list(self.task1.links_set.all()), [self.links])


class DeletionTests(TestCase):

    def setUp(self):
        self.project1 = Project.objects.create()
        self.project2 = Project.objects.create()
        self.links = Links.objects.create()

    def test_delete_src(self):
        self.links.related_objects = [self.project1, self.project2]
        self.links.save()
        self.links.delete()
        self.assertEqual(self.project1.links_set.count(), 0)
        self.assertEqual(self.project2.links_set.count(), 0)

    def test_delete_tgt(self):
        self.links.related_objects = [self.project1, self.project2]
        self.links.save()
        self.project2.delete()
        self.assertEqual(self.links.related_objects.count(), 1)
