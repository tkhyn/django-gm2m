"""
See issue #4
"""

from .. import base


class ValidationTests(base.TestCase):

    other_apps = ('norevrel',)

    # test_check and test_deconstruct will be run
