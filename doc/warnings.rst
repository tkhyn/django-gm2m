.. _warnings:

Warnings
========


(De)Serialization
-----------------

Since version 0.4.2, ``django-gm2m`` supports serialization and deserialisation
to and from fixture files (JSON, XML, YAML ...) using the ``dumpdata`` and
``loaddata`` management commands.


``dumpdata`` and natural keys
.............................

As you probably already know, ``django-gm2m`` relies on
``django.contrib.contenttypes`` and needs to link ``ContentType`` objects. If
you use the ``dumpdata`` command without excluding the ``contenttypes`` app and
with standard primary/foreign keys, the data will contain dumped ``ContentType``
objects which will be referenced by their standard primary key (an integer).

When you'll attempt to load that data using ``loaddata``, Django will at the
same attempt to recreate the needed ``ContentType`` objects, which primary
keys may not be consistent with your data, therefore raising a fixture loading
error.

To avoid that, it is advised to use the ``dumpdata`` command with the following
options in a project that makes use of ``django-gm2m``:

   - ``--natural-primary --natural-foreign`` to use natural keys instead of 
     actual primary keys in the dumped data (the natural key for a contenttype 
     is, for example, ``'app_name.modelname'``)
   - ``-e contenttypes`` to exclude the ``ContentType`` objects from the dumped
     data. These objects are automatically recreated by django anyway

See this `StackOverflow question and answers`_ for more details.


Custom serializers
..................

When a project using ``django-gm2m`` is initialized, the default django
serializers (namely ``json``, ``xml``, ``yaml``) are overridden by specific
serializers that have been tuned to work with ``GM2MField``.

This means that in case you have custom serializers in your project or app,
you will need to derive them from ``gm2m.serializers.*.Serializer`` instead of
``django.core.serializers.*.Serializer`` (same for ``Deserializer``). If you
don't do that, (de)serialization of ``GM2MFields`` will not work.


.. _`StackOverflow question and answers`: http://stackoverflow.com/questions/853796/problems-with-contenttypes-when-loading-a-fixture-in-django
