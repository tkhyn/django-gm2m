"""
See issue #4
"""

from django.core.management import call_command

from .. import base


class ValidationTests(base.TestCase):

    other_apps = ('norevrel',)

    def test_check(self):
        call_command('check')
