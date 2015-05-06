"""
Failing tests for issue #8 regarding prefetching with primary keys of different
types in the linked models
"""

from datetime import date, time

from .. import base


class ExoticPKPrefetchTests(base.TestCase):

    def setUp(self):
        self.task = self.models.DailyTask.objects.create(time=time(12))
        self.day = self.models.Day.objects.create(date=date.today())

        self.day.tasks.add(self.task)


    def test_forward(self):
        self.assertEqual(
            self.models.Day.objects.prefetch_related('tasks')[0], self.day
        )

    def test_reverse(self):
        self.assertEqual(
            self.models.DailyTask.objects.prefetch_related('days')[0],
            self.task
        )
