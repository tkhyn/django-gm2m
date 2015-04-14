import django

from ..app.models import Project
from .models import Links

from .. import base


@base.skipIf(django.VERSION < (1, 6),
             'No deletion customisation for Django < 1.6')
class CustomDeletionTests(base.TestCase):

    def setUp(self):
        self.project1 = Project.objects.create()
        self.project2 = Project.objects.create()
        self.links = Links.objects.create()

    def test_delete_src(self):
        self.links.related_objects = [self.project1, self.project2]
        self.links.delete()
        # no more Links instances
        self.assertEqual(Links.objects.count(), 0)
        # but the through model instances have not been deleted
        self.assertEqual(self.project1.links_set.through.objects.count(), 2)

    def test_delete_tgt(self):
        self.links.related_objects = [self.project1, self.project2]
        self.project1.delete()
        self.project2.delete()
        # no more Project instances
        self.assertEqual(Project.objects.count(), 0)
        # but the through model instances have not been deleted
        self.assertEqual(self.links.related_objects.through.objects.count(), 2)
