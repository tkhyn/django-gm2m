from ..app.models import Project
from .models import Links

from .. import base


class RelatedNameTests(base.TestCase):

    def setUp(self):
        self.project = Project.objects.create()
        self.links = Links.objects.create()

    def test_related_accessor(self):
        self.links.related_objects.add(self.project)
        self.assertEqual(self.project.related_links.count(), 1)
        self.assertIn(self.links, self.project.related_links.all())
