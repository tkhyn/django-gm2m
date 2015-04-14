from .. import base


class MultipleRelatedTests(base.TestCase):

    def setUp(self):
        self.project = self.models.Project.objects.create()
        self.links = self.models.Links.objects.create()

    def test_related_accessor(self):
        self.assertEqual(self.project.links_set.count(), 0)
        self.links.related_objects.add(self.project)
        self.assertEqual(self.project.links_set.count(), 1)
        self.assertIn(self.links, self.project.links_set.all())
