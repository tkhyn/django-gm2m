from collections import defaultdict

from django import test

from .models import Links


# nose should not look for tests in this module
__test__ = False
__unittest = True


class TestCase(test.TestCase):

    to_link = ()

    def setUp(self):

        indexes = defaultdict(lambda: 0)
        for o in self.to_link:
            indexes[o] += 1
            att_name = o.__name__.lower() + str(indexes[o])
            obj = o()
            obj.save()
            setattr(self, att_name, obj)

        self.links = Links()
        self.links.save()
