from .models import Project, Task

from .base import TestCase


class LinksTests(TestCase):

    to_link = (Project, Task, Task)

    def test_add(self):
        self.links.related_objects.add(self.project1)
        self.links.save()
        self.assertIn(self.project1, self.links.related_objects.all())

    def test_set(self):
        self.links.related_objects = [self.project1]
        self.assertEqual(self.links.related_objects.count(), 1)
        self.assertEqual(self.links.related_objects.all()[0], self.project1)

    def test_remove(self):
        self.links.related_objects = [self.project1, self.task1]
        self.links.related_objects.remove(self.project1)
        self.assertEqual(self.links.related_objects.count(), 1)
        self.assertEqual(self.links.related_objects.all()[0], self.task1)
