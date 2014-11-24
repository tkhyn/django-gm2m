from .. import base

from ..app.models import Project
from .models import Links, RelLinks


class ThroughFieldTests(base.TestCase):

    def setUp(self):
        self.project1 = Project.objects.create()
        self.links = Links.objects.create()
        self.rellink = RelLinks.objects.create(links=self.links,
                                               target=self.project1)

    def test_accessors(self):
        self.assertListEqual([self.links], list(self.project1.links_set.all()))
        self.assertListEqual([self.project1],
                             list(self.links.related_objects.all()))

    def test_through_fields(self):
        self.assertDictEqual(
            RelLinks._meta._field_names,
            {'src': 'links',
             'tgt': 'target',
             'tgt_ct': 'target_ct',
             'tgt_fk': 'target_fk'})
