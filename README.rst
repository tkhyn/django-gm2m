django-gm2m
===========

|copyright| 2014-2020 Thomas Khyn

Django generic many-to-many field implementation.

This django application exposes a ``GM2MField`` that combines
the features of the standard Django ``ManyToManyField`` and
``GenericForeighKey`` and that can be used exactly the same way.

It has been tested with Django 2.2.*, 3.0.*, 3.1.*, 3.2.*, 4.0.* and their matching Python versions (3.7 to 3.10).

If you like django-gm2m and find it useful, you may want to thank me and
encourage future development by sending a few mBTC / mBCH / mBSV at this address:
``1EwENyR8RV6tMc1hsLTkPURtn5wJgaBfG9``.


Features
--------

- Works like the built-in Django related fields
- Creates one table per relation, like ``ManyToManyField``, and not one big
  table linking anything to anything (django-generic-m2m_'s default approach)
- No need to modify nor monkey-patch the existing model classes that need to be
  linked
- Automatic reverse relations when an instance is added
- Related objects prefetching
- Through models support
- Deletion behaviour customization using signals
- Migrations support


Documentation
-------------

The documentation is hosted on readthedocs_. You'll find a quick start and
the description of all django-gm2m's advanced features.



.. |copyright| unicode:: 0xA9

.. _django-generic-m2m: https://pypi.python.org/pypi/django-generic-m2m
.. _readthedocs: http://django-gm2m.readthedocs.io/en/stable
