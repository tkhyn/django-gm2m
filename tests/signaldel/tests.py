import django
from django.utils.unittest import skipIf

from mock_django.signals import mock_signal_receiver

from gm2m.signals import deleting_src, deleting_tgt

from ..app.models import Project
from .models import Links

from ..base import TestCase


@skipIf(django.VERSION < (1, 6), 'No deletion customisation for Django < 1.6')
class SignalDeletionTests(TestCase):

    def setUp(self):
        self.project1 = Project.objects.create()
        self.project2 = Project.objects.create()
        self.links = Links.objects.create()

    def test_delete_src(self):
        self.links.related_objects = [self.project1, self.project2]

        with mock_signal_receiver(deleting_src) as on_delete:
            self.links.delete()
            self.assertEqual(on_delete.call_count, 1)

        # no more Links instances
        self.assertEqual(Links.objects.count(), 0)
        # and the through model instances have been deleted
        self.assertEqual(self.project1.links_set.through.objects.count(), 0)

    def test_group_delete_src(self):
        self.links.related_objects = [self.project1]
        links2 = Links.objects.create()
        links2.related_objects = [self.project2]

        with mock_signal_receiver(deleting_src) as on_delete:
            Links.objects.all().delete()
            self.assertEqual(on_delete.call_count, 1)

        # no more Links instances
        self.assertEqual(Links.objects.count(), 0)
        # and the through model instances have been deleted
        self.assertEqual(self.project1.links_set.through.objects.count(), 0)

    def test_delete_tgt(self):
        self.links.related_objects = [self.project1, self.project2]

        with mock_signal_receiver(deleting_tgt) as on_delete:
            self.project1.delete()
            self.assertEqual(on_delete.call_count, 1)

        # no more Project instances
        self.assertEqual(Project.objects.count(), 1)
        # and the through model instances have been deleted
        self.assertEqual(self.links.related_objects.through.objects.count(), 1)

    def test_group_delete_tgt(self):
        self.links.related_objects = [self.project1, self.project2]

        with mock_signal_receiver(deleting_tgt) as on_delete:
            Project.objects.all().delete()
            self.assertEqual(on_delete.call_count, 1)

        # no more Project instances
        self.assertEqual(Project.objects.count(), 0)
        # and the through model instances have been deleted
        self.assertEqual(self.links.related_objects.through.objects.count(), 0)
