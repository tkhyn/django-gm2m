from __future__ import absolute_import

from .. import base


class RelatedNameTests(base.TestCase):

    def setUp(self):
        self.project = self.models.Project.objects.create()
        self.links = self.models.Links.objects.create()

    def test_related_accessor(self):
        self.links.related_objects.add(self.project)
        self.assertEqual(self.project.related_links.count(), 1)
        self.assertIn(self.links, self.project.related_links.all())
