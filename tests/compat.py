import django

__test__ = False

try:
    from unittest import mock
except ImportError:
    # Python 2
    import mock
