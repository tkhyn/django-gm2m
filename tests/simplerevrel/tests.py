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

    def test_not_in_reverse_rel_option_fields(self):
        """
        Check that the reverse relation is not in the Project's options fields
        """

        self.assertNotIn(self.models.Project._meta.virtual_fields[0],
                         self.models.Project._meta.fields)

    def test_get_gm2m_models(self):
        self.assertListEqual(
            self.models.Links.related_objects.get_related_models(),
            [self.models.Project]
        )

        self.links.related_objects.add(self.models.Task.objects.create())

        self.assertListEqual(
            self.models.Links.related_objects.get_related_models(),
            [self.models.Project]
        )
        self.assertListEqual(
            self.models.Links.related_objects.get_related_models(
                include_auto=True
            ),
            [self.models.Project, self.models.Task]
        )


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


class FilterTests(base.TestCase):

    def setUp(self):
        self.links = self.models.Links.objects.create(name='Links')
        self.project = self.models.Project.objects.create()
        self.links.related_objects.add(self.project)

    def test_filter_by_model(self):
        self.assertListEqual(
            list(self.links.related_objects.filter(Model=self.models.Project)),
            [self.project],
        )
        self.assertListEqual(
            list(self.links.related_objects.filter(Model='app.Project')),
            [self.project],
        )
        self.assertListEqual(
            list(self.links.related_objects.filter(Model=self.models.Task)),
            [],
        )

        task = self.models.Task.objects.create()
        self.links.related_objects.add(task)

        self.assertSetEqual(
            set(self.links.related_objects.filter(
                Model__in=(self.models.Project, self.models.Task))),
            {self.project, task},
        )

    def test_reverse_chain_filter(self):
        self.assertEqual(
            self.models.Project.objects.filter(links__name='Links')[0],
            self.project)


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
        # 5 projects, 5 tasks per project, 5 links instance
        projects = [self.models.Project.objects.create() for p in range(5)]
        tasks = [[self.models.Task.objects.create() for t in range(5)]
                 for g in range(5)]
        links = [self.models.Links.objects.create() for l in range(5)]

        for l, p, t in zip(links, projects, tasks):
            l.related_objects = [p] + t

    def test_prefetch_forward(self):

        with self.assertNumQueries(4):
            # 4 queries:
            # - 1 for all the Links instances
            # - 1 for all the through model instances
            # - 1 for all the Project instances
            # - 1 for all the Task instances
            prefetched = [set(l.related_objects.all()) for l
                          in self.models.Links.objects \
                                 .prefetch_related('related_objects')]

        with self.assertNumQueries(16):
            # without prefetching, we have 16 queries instead of 4!
            # - 1 for all the Links instances
            # - 3 for each of the 5 links (1 for the through model + 1 for the
            #   project + 1 for the tasks)
            normal = [set(l.related_objects.all())
                      for l in self.models.Links.objects.all()]

        self.assertEqual(prefetched, normal)

    def test_prefetch_reverse(self):

        with self.assertNumQueries(2):
            # only 2 queries here:
            # - 1 to retrieve the tasks
            # - 1 to retrieve all the links related to the projects via the
            #   through model
            # Note: if the ContentType's cache is cleared beforehand, it will
            # take 3 queries as it will retrieve the Project content type
            prefetched = [set(t.links_set.all()) for t
                          in self.models.Task.objects \
                                 .prefetch_related('links_set')]

        with self.assertNumQueries(26):
            # without prefetching we have 26 queries instead of 2!!
            # - 1 for all tasks
            # - 1 for each of the 25 tasks (for the links)
            normal = [set(t.links_set.all())
                      for t in self.models.Task.objects.all()]

        self.assertEqual(prefetched, normal)
