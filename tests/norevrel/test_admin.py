from django.contrib.admin.sites import AdminSite
from django.contrib.admin import ModelAdmin

from .. import base

from .models import Links


class MockRequest(object):
    pass


class AdminTests(base.TestCase):

    def setUp(self):
        self.site = AdminSite()
        self.model_admin = ModelAdmin(Links, self.site)
        self.links = self.models.Links.objects.create()

    def test_admin(self):
        form = self.model_admin.get_form(MockRequest(), self.links)(
            instance=self.links, data={
                'related_objects': []
            }
        )
        self.assertTrue(form.is_valid())
