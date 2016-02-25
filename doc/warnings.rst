.. _warnings:

Warnings
========


(De)Serialization
-----------------

Since version 0.4.2, ``django-gm2m`` supports serialization and deserialisation
to and from fixture files (JSON, XML, YAML ...) using the ``dumpdata`` and
``loaddata`` management commands.

When a project using ``django-gm2m`` is initialized, the default django
serializers (namely ``json``, ``xml``, ``yaml``) are overridden by specific
serializers that have been tuned to work with ``GM2MField``.

This means that in case you have custom serializers in your project or app,
you will need to derive them from ``gm2m.serializers.*.Serializer`` instead of
``django.core.serializers.*.Serializer`` (same for ``Deserializer``). If you
don't do that, (de)serialization of ``GM2MFields`` will not work.
