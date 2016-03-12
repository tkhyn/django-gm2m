from .. import base


class AbstractBaseTests(base.TestCase):

    def test_reverse_relation(self):
        self.assertTrue(hasattr(self.models.Project, 'basiclinks_set'))

    def test_subclasses(self):

        project = self.models.Project.objects.create()
        task = self.models.Task.objects.create()

        bas_links = self.models.BasicLinks.objects.create()
        enh_links = self.models.EnhancedLinks.objects.create()

        bas_links.related_objects.add(project)
        enh_links.related_objects.add(task)

        self.assertEqual(bas_links.related_objects.all()[0], project)
        self.assertEqual(enh_links.related_objects.all()[0], task)
