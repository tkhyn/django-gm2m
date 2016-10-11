django-gm2m - changes
=====================

key:
| \* bug fix
| \+ addition
| \- deletion


v0.4 (03-01-2016)
-----------------

| \+ Django 1.9 support
| \- Drops Django < 1.8 support

v0.4.1 (29-01-2016)
...................

| \* Eliminates Django 1.10 deprecation warnings (#16)
| \* Fixes the documentation regarding INSTALLED_APPS (#18)
| \* Doc typos

v0.4.2 (29-02-2016)
...................

| \+ Django 1.10 compatibility (#19)
| \+ Adds serialization / deserialization support (#21)
| \* Fixes instantiation in abstract models (#22)
| \* Fixes installation issue with newest setuptools (#23)

v0.4.3 (01-04-2016)
...................

| \+ Adds GM2MField.get_related_models method (#26)
| \* Improves documentation (#25)
| \* Fixes wrong reverse related manager superclass (#27)
| \* Fixes reverse relations not created when using abstract model (#24)

v0.4.4 (27-06-2016)
-------------------

| \* Fixes GM2MTo integration (#29)

v0.4.5 (13-08-2016)
...................

| \+ Supports sorting (#30)
| \+ Django 1.10+ compatibility (deprecation warnings)
| \* Backport of properties renamed in Django 1.9 and 1.10
| \* Fixes content types cache accessor for Django 1.8.10+

v0.4.6 (21-08-2016)
...................

| \* Fixes setup.py requirement excluding django 1.10 (PR #1, thanks @iblag)

v0.4.7 (11-10-2016)
-------------------

| \* Fixes deconstruction issue when relation attributes are modified externally


v0.3 (09-09-2015)
-----------------

| \+ Django 1.4, 1.5 and 1.6 are no longer supported
| \+ The documentation is now on Read The Docs
| \+ Adds ability to filter a GM2M queryset by model(s)
| \* Fixes issue with fake content type models (#14)
| \* Fixes default value asked by makemigrations (#12)
| \* Fixes various minor issues with Django 1.7


v0.2 (25-11-2014)
-----------------

| \+ Full Django 1.7+ migration support
| \+ through_fields option support
| \+ System checks (Django 1.7)

v0.2.1 (25-11-2014)
...................

| \* m2m_db_table method bug
| \* related_name type in deconstruct (see Django ticket #23455)

v0.2.2 (05-12-2014)
...................
| \* related models lazy lookup bug (issue #1)

v0.2.3 (14-12-2014)
...................
| \* issue with through model fields alteration in Django 1.7+ migrations
| \+ pk_maxlength option to set the max length of the primary key to a user-defined value

v.0.2.4 (14-04-2015)
....................
| \* fixes issue when creating ModelForms for related models
| \* Django 1.8 compatibility:
|    \* add_virtual_field issue (issue #2)
|    \* GM2MField's column is None
|    \* fixes deprecation warnings regarding renamed django modules removed in django 1.9

v.0.2.5 (14-04-2015)
....................
| \* fixes migration problems when using complex relations between models (issue #3)

v.0.2.6 (29-04-2015)
....................
| \* Fixes system checks failure after ``add_relation`` (#4)
| \* Fixes migration problems with combined M2M and GM2M (#5)
| \* Fixes ``BaseDatabaseSchemaEditor`` import with Django 1.8 (#6)
| \* Fixes missing field flags on ``GM2MRelation`` and missing attributes on ``GM2MRel`` / ``GM2MUnitRel`` (#7)

v.0.2.7 (09-05-2015)
....................
| \* Fixes primary key lookups in fwd and reverse prefetching (#8)
| \* Fixes migrations application on a migrated app (#9)
| \* Fixes ``contenttypes.ContentType`` dependency in migrations (#10)

v.0.2.8 (01-06-2015)
....................
| \+  Adds reverse chained lookup in queries (#11)


v0.1 (08-10-2014)
-----------------

| \+ Automatic and explicitly defined reverse relations
| \+ Related objects prefetching
| \+ Through models
| \+ Deletion behaviour customization (Django 1.6+)
| \+ Extended compatibility (Django 1.4 to 1.7, Python 2.6 to 3.4)

v0.1.1 (21-11-2014)
...................

| \* Inheritance of models with GM2MField no longer causes issues in Django 1.7


v0.0 (13-08-2014)
-----------------

| \+ Birth
