from ..models import Project
from .models import Links

from ..base import TestCase


class LinksTests(TestCase):

    def setUp(self):
        self.project = Project.objects.create()
        self.links = Links.objects.create()

    def test_related_accessor(self):
        self.links.related_objects.add(self.project)
        self.links.save()
        self.assertIn(self.links, self.project.links_set.all())
