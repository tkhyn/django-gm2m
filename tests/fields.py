from .models import Project, Task

from .base import TestCase


class LinksTests(TestCase):

    to_link = (Project, Task, Task)

    def test_add(self):
        self.links.related_objects.add(self.project1)
        self.links.save()
        self.assertIn(self.project1, self.links.related_objects.all())
