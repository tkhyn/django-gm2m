"""
This module patches older versions of django to expose properties that were
renamed in later versions.

This could of course create problems if another app patches these properties
differently but it's the likeliness of this to happen is so low that it should
not be an issue
"""


import django
from django.db.models.query_utils import PathInfo


if django.VERSION < (2, 0):
    from collections import namedtuple
    PathInfo = namedtuple('PathInfo', PathInfo._fields + ('filtered_relation',))
