import os
import json

from django.core.management import call_command

import xmltodict
import yaml

from .. import base


class FixtureTests(base.TestCase):

    def fixture_file(self, name):
        return os.path.join(os.path.dirname(__file__), 'fixtures', name)

    def dump(self, fmt, to_data):
        dump = self.fixture_file('dump.' + fmt)
        ref = self.fixture_file('reference.' + fmt)

        try:
            project = self.models.Project.objects.create()
            links = self.models.Links.objects.create()
            links.related_objects.add(project)

            call_command('dumpdata', 'app', 'norevrel',
                         format=fmt, output=dump)

            dumpdata = to_data(open(dump, 'r'))
            refdata = to_data(open(ref, 'r'))

            self.assertEqual(dumpdata, refdata)

        finally:
            try:
                os.remove(dump)
            except OSError:
                pass

    def load(self, fmt):
        call_command('loaddata', 'reference.' + fmt)
        links = self.models.Links.objects.all()[0]
        project = self.models.Project.objects.all()[0]
        self.assertIn(project, links.related_objects.all())

    def test_dump_json(self):
        self.dump('json', json.load)

    def test_load_json(self):
        self.load('json')

    def test_dump_xml(self):
        self.dump('xml', lambda f: xmltodict.parse(f.read(),
                                                   dict_constructor=dict))

    def test_load_xml(self):
        self.load('xml')

    def test_dump_yaml(self):
        self.dump('yaml', yaml.load)

    def test_load_yaml(self):
        self.load('yaml')
