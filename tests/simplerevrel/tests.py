from ..app.models import Project, Task
from .models import Links

from ..base import TestCase


class LinksTests(TestCase):

    def setUp(self):
        self.project = Project.objects.create()
        self.links = Links.objects.create()

    def test_related_accessor(self):
        self.links.related_objects.add(self.project)
        self.links.save()
        self.assertEqual(self.project.links_set.count(), 1)
        self.assertIn(self.links, self.project.links_set.all())

    def test_add_relation(self):
        """
        Adds a reverse relation to a GM2MField after an object has been added
        """
        task = Task.objects.create()
        self.links.related_objects.add(task)
        Links.related_objects.add_relation(Task)
        self.assertEqual(task.links_set.count(), 1)
        self.assertIn(self.links, task.links_set.all())


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
        self.assertNotIn(self.project2, self.links.related_objects.all())
