from __future__ import absolute_import

import django
from django.core.management import call_command


__test__ = False

try:
    from unittest import mock
except ImportError:
    # Python 2
    import mock


if django.VERSION >= (1, 9):
    def syncdb(**kwargs):
        call_command('migrate', run_syncdb=True, **kwargs)
else:
    # Django 1.8 has no 'run_syncdb' option
    def syncdb(**kwargs):
        call_command('syncdb', **kwargs)
