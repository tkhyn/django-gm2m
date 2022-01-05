from __future__ import absolute_import


__test__ = False


try:
    # Django 3+
    from django.urls import re_path
except ImportError:
    # Django 2
    from django.conf.urls import url as re_path
