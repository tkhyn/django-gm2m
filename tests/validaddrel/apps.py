from __future__ import absolute_import

from django.apps import AppConfig


class AddRelationAppConfig(AppConfig):

    name = 'tests.validaddrel'
    verbose_name = 'to test validation after add_relation (#4)'

    def ready(self):
        from tests.norevrel.models import Links
        from tests.app.models import Project
        from .models import Milestone

        Links.related_objects.add_relation(Project)
        Links.related_objects.add_relation(Milestone)
