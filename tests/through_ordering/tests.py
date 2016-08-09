from .. import base


class ThroughOrderingTests(base.TestCase):

    def setUp(self):
        self.links = self.models.Links.objects.create()
        self.items = []
        for i in range(10):
            project = self.models.Project.objects.create()
            task = self.models.Task.objects.create()
            self.items.extend((project, task))
            self.models.RelLinks.objects.create(links=self.links, target=project, order=2 * i)
            self.models.RelLinks.objects.create(links=self.links, target=task, order=2 * i + 1)

    def test_ordering(self):
        self.assertListEqual(list(self.links.related_objects.all()), self.items)

    def test_order_by(self):
        self.assertListEqual(list(self.links.related_objects.order_by('-order')), list(reversed(self.items)))
