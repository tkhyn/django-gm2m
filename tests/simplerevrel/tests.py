from ..models import Project, Task
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
