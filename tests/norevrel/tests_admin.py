import warnings

from django.contrib.admin.sites import AdminSite
from django.contrib.admin import ModelAdmin

from .. import base


class MockRequest(object):
    pass


class AdminTests(base.TestCase):

    def setUp(self):
        self.site = AdminSite()
        self.model_admin = ModelAdmin(self.models.Links, self.site)
        self.links = self.models.Links.objects.create()

    def test_formfield_warning(self):
        with self.assertRaises(FutureWarning), warnings.catch_warnings():
            warnings.filterwarnings('error', category=FutureWarning)
            self.model_admin.get_form(MockRequest(), self.links)()

    def test_admin(self):
        form = self.model_admin.get_form(MockRequest(), self.links)(
            instance=self.links, data={
                'related_objects': ''
            }
        )
        self.assertTrue(form.is_valid())

    def test_submit_form(self):
        self.links.related_objects = [
            self.models.Project.objects.create(),
            self.models.Task.objects.create()
        ]

        form = self.model_admin.get_form(MockRequest(), self.links)(
            instance=self.links, data={
                'related_objects': ''
            }
        )
        form.save()

        self.assertEqual(self.links.related_objects.all().count(), 2)
