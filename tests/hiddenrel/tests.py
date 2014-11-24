from ..app.models import Project
from .models import Links

from .. import base


class ReverseRelationTests(base.TestCase):

    def setUp(self):
        self.links = Links.objects.create()
        self.project = Project.objects.create()
        self.links.related_objects.add(self.project)

    def test_reverse_access(self):
        self.assertTrue(Links.related_objects.field.rel.rels[0].is_hidden())
        with self.assertRaises(AttributeError):
            getattr(self.project, 'related_links+')


class HiddenRelDeletionTests(base.TestCase):
    """
    Checks that cascading deletion works with hidden related fields
    """

    def setUp(self):
        self.project1 = Project.objects.create()
        self.project2 = Project.objects.create()
        self.links = Links.objects.create()

    def test_delete_src(self):
        self.links.related_objects = [self.project1, self.project2]
        self.links.delete()
        self.assertEqual(
            Links.related_objects.through._default_manager.count(), 0)

    def test_delete_tgt(self):
        self.links.related_objects = [self.project1, self.project2]
        self.project2.delete()
        self.assertEqual(
            Links.related_objects.through._default_manager.count(), 1)
        self.assertEqual(self.links.related_objects.count(), 1)
