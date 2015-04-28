import django

from .. import base


class RelatedTests(base.TestCase):

    def setUp(self):
        self.project = self.models.Project.objects.create()
        self.links = self.models.Links.objects.create()

    def test_related_accessor(self):
        self.assertEqual(self.project.links_set.count(), 0)
        self.links.related_objects.add(self.project)
        self.assertEqual(self.project.links_set.count(), 1)
        self.assertIn(self.links, self.project.links_set.all())

    def test_add_relation(self):
        """
        Adds a reverse relation to a GM2MField after an object has been added
        """
        task = self.models.Task.objects.create()
        self.links.related_objects.add(task)
        self.models.Links.related_objects.add_relation(self.models.Task)
        self.assertEqual(task.links_set.count(), 1)
        self.assertIn(self.links, task.links_set.all())

    @base.skipIf(django.VERSION < (1, 7),
        'reverse relation is not added to virtual_fields in django < 1.7')
    def test_not_in_reverse_rel_option_fields(self):
        """
        Check that the reverse relation is not in the Project's options fields
        """

        self.assertNotIn(self.models.Project._meta.virtual_fields[0],
                         self.models.Project._meta.fields)


class ReverseOperationsTest(base.TestCase):

    def setUp(self):
        self.links1 = self.models.Links.objects.create()
        self.links2 = self.models.Links.objects.create()
        self.project = self.models.Project.objects.create()
        self.links1.related_objects.add(self.project)

    def test_reverse_add(self):
        self.project.links_set.add(self.links2)
        self.assertListEqual(list(self.links2.related_objects.all()),
                             [self.project])

    def test_reverse_remove(self):
        self.links2.related_objects.add(self.project)
        self.project.links_set.remove(self.links2)
        self.assertEqual(self.links2.related_objects.count(), 0)

    def test_reverse_clear(self):
        self.links2.related_objects.add(self.project)
        self.project.links_set.clear()
        self.assertEqual(self.links1.related_objects.count(), 0)
        self.assertEqual(self.links2.related_objects.count(), 0)


class DeletionTests(base.TestCase):

    def setUp(self):
        self.project1 = self.models.Project.objects.create()
        self.project2 = self.models.Project.objects.create()
        self.links = self.models.Links.objects.create()

    def test_delete_src(self):
        self.links.related_objects = [self.project1, self.project2]
        self.links.delete()
        self.assertEqual(self.project1.links_set.count(), 0)
        self.assertEqual(self.project2.links_set.count(), 0)

    def test_delete_tgt(self):
        self.links.related_objects = [self.project1, self.project2]
        self.project2.delete()
        self.assertEqual(self.links.related_objects.count(), 1)


class PrefetchTests(base.TestCase):

    def setUp(self):
        self.project = self.models.Project.objects.create()
        self.task = self.models.Task.objects.create()
        self.links1 = self.models.Links.objects.create()
        self.links2 = self.models.Links.objects.create()

        self.links1.related_objects = [self.project, self.task]

        self.links2.related_objects = [self.project]

    def test_prefetch_forward(self):
        with self.assertNumQueries(4):
            # 4 queries = 2 queries to retrieve the through models +
            # one query for each related model type (Project, Task)
            # without prefetching it takes 6 queries
            prefetched = [list(l.related_objects.all()) for l
                          in self.models.Links.objects \
                                 .prefetch_related('related_objects')]

        # without prefetching, we indeed have 6 queries instead of 4
        normal = [list(l.related_objects.all())
                        for l in self.models.Links.objects.all()]

        self.assertListEqual(prefetched, normal)

    def test_prefetch_reverse(self):
        with self.assertNumQueries(2):
            # much more efficient this way as there are no supplementary
            # queries due to the generic foreign key
            prefetched = [list(p.links_set.all()) for p
                          in self.models.Project.objects \
                                 .prefetch_related('links_set')]

        normal = [list(p.links_set.all())
                  for p in self.models.Project.objects.all()]
        self.assertEqual(prefetched, normal)
