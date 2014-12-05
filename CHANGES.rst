django-gm2m - changes
=====================


v0.3 (dev)
----------

Todo:
- admin


v0.2 (25-11-2014)
-----------------

Added:
- Full Django 1.7+ migration support
- through_fields option support
- System checks (Django 1.7)

v0.2.1 (25-11-2014)
...................
- fixed: m2m_db_table method bug
- fixed: related_name type in deconstruct (see Django ticket #23455)

v0.2.2 (05-12-2014)
...................
- fixed: related models lazy lookup bug (issue #1)


v0.1 (08-10-2014)
-----------------

Features:
- Automatic and explicitly defined reverse relations
- Related objects prefetching
- Through models
- Deletion behaviour customization (Django 1.6+)
- Extended compatibility (Django 1.4 to 1.7, Python 2.6 to 3.4)

v0.1.1 (21-11-2014)
...................

Bugfix:
- Inheritance of models with GM2MField no longer causes issues in Django 1.7


v0.0 (13-08-2014)
-----------------

- Birth
