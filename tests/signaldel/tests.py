from gm2m.signals import deleting

from .. import base
from ..mock import mock_signal_receiver


class SignalDeletionTests(base.TestCase):

    def setUp(self):
        self.project1 = self.models.Project.objects.create()
        self.project2 = self.models.Project.objects.create()
        self.links = self.models.Links.objects.create()

    def test_delete_src(self):
        self.links.related_objects = [self.project1, self.project2]

        with mock_signal_receiver(deleting) as on_delete:
            self.links.delete()
            self.assertEqual(on_delete.call_count, 1)

        # no more Links instances
        self.assertEqual(self.models.Links.objects.count(), 0)
        # and the through model instances have been deleted
        self.assertEqual(self.project1.links_set.through.objects.count(), 0)

    def test_group_delete_src(self):
        self.links.related_objects = [self.project1]
        links2 = self.models.Links.objects.create()
        links2.related_objects = [self.project2]

        with mock_signal_receiver(deleting) as on_delete:
            self.models.Links.objects.all().delete()
            self.assertEqual(on_delete.call_count, 1)

        # no more Links instances
        self.assertEqual(self.models.Links.objects.count(), 0)
        # and the through model instances have been deleted
        self.assertEqual(self.project1.links_set.through.objects.count(), 0)

    def test_delete_tgt(self):
        self.links.related_objects = [self.project1, self.project2]

        with mock_signal_receiver(deleting) as on_delete:
            self.project1.delete()
            self.assertEqual(on_delete.call_count, 1)

        # only 1 Project instance left
        self.assertEqual(self.models.Project.objects.count(), 1)
        # and the through model instance has not been deleted
        self.assertEqual(self.links.related_objects.through.objects.count(), 1)

    def test_group_delete_tgt(self):
        self.links.related_objects = [self.project1, self.project2]

        with mock_signal_receiver(deleting) as on_delete:
            self.models.Project.objects.all().delete()
            self.assertEqual(on_delete.call_count, 1)

        # no more Project instances
        self.assertEqual(self.models.Project.objects.count(), 0)
        # and the through model instances have been deleted
        self.assertEqual(self.links.related_objects.through.objects.count(), 0)
