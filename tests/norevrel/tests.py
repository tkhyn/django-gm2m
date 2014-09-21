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
