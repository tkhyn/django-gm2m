from ..app.models import Project, Task
from .models import Links

from ..base import TestCase


class NoRevRelTests(TestCase):

    def setUp(self):
        self.project = Project.objects.create()
        self.task1 = Task.objects.create()
        self.task2 = Task.objects.create()
        self.links = Links.objects.create()


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
