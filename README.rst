django-gm2m
===========

|copyright| 2014 Thomas Khyn

Django generic many-to-many field implementation.

This django application exposes a ``GM2MField`` that combines
the features of the standard Django ``ManyToManyField`` and
``GenericForeighKey`` and that can be used exactly the same way.

It works with Django 1.4 to 1.7 and matching Python versions (2.6 to 3.4).


Features
--------

- Works like the built-in Django related fields
- Creates only one table per relation, like ``ManyToManyField``
- No need to modify the existing model classes that need to be linked
- Reverse relations ``<model_name>_set``
- Related objects prefetching
- Deletion behaviour customization (Django 1.6+)


Installation
------------

As straightforward as it can be, using ``pip``::

   pip install django-gm2m

You then need to add ``gm2m`` to your ``INSTALLED_APPS``.

You will also need to have ``django.contrib.contenttypes`` enabled.


Quick start
-----------

You can use the exposed ``GM2MField`` exactly the same way as a
``ManyToManyField``.

Suppose you have some models describing videos types::

   from django.db import models

   class Video(models.Model):
      pass

   class Movie(Video):
      pass

   class Documentary(Video):
      pass

Now, if you want to have a field for the preferred videos of a User, you simply
need to add a default ``GM2MField`` to the ``User`` model::

   class User(models.Model):
      preferred_videos = GM2MField()

Now you can add videos to the preferred_videos set::

   user = User.objects.create()
   movie = Movie.objects.create()

   user.preferred_videos.add(movie)

or::

   user.preferred_videos = [movie]

You can obviously mix instances from different models::

   documentary = Documentary.objects.create()
   user.preferred_videos = [movie, documentary]


Relations
---------

From a ``User`` instance, you can now fetch all the user's preferred videos::

   >>> list(user.preferred_videos)
   [<Movie object>, <Documentary object>]

However, when using a default ``GM2MField()`` (without arguments), it does not
create any reverse relations. This means that, from a ``Movie`` instance, you
cannot retrieve the users who have this instance in their ``preferred_videos``
using::

   >>> list(movie.user_set)
   AttributeError: 'Movie' object has no attribute 'user_set'

To enable this behaviour, you need to let the ``GM2MField`` constructor know
that you want it to create a reverse relation with given models. To do so, you
simply need to provide the models as arguments. You may use model names if
necessary to avoid circular imports::

   class User(models.Model):
      preferred_videos = GM2MField(Movie, 'Documentary')

Note that this will not prevent the addition of instances from any other models
to the generic many-to-many field. This only creates reverse relations.


Deletion
--------

When an instance of an unrelated model is deleted, no relation is deleted, as
the unrelated model has no way to know (yet) that one of its instances has
been added to a Many-to-Many relation.

By default, when an instance from a related model or source model  is deleted,
all relations to this instance are deleted. It is possible, from Django 1.6, to
change this behavior by using the ``on_delete``, ``on_delete_src`` and
``on_delete_tgt`` keyword arguments when creating the GM2M field::

   from gm2m.deletion import DO_NOTHING

   class User(models.Model):
      preferred_videos = GM2MField(Movie, 'Documentary', on_delete=DO_NOTHING)

If you only want this behaviour on one side of the relationship (e.g. on the
source model side), use ``on_delete_src``::

   class User(models.Model):
      preferred_videos = GM2MField(Movie, 'Documentary',
                                   on_delete_src=DO_NOTHING)

``on_delete_src`` and ``on_delete_tgt`` override ``on_delete``.

The only customisation is - for the moment - to use the ``DO_NOTHING``
function. When using ``DO_NOTHING``, the relation is not deleted with the
related instance. It is your responsibility to ensure that the database
remains consistent after the deletion operation.


Prefetching
-----------

Prefetching works exactly the same way as with django ``ManyToManyField``::

   user.objects.prefetch_related('preferred_videos')

will, in a minimum number of queries, prefetch all the videos in all the user's
``preferred_video`` lists.


Through models
--------------

Through models are also supported. The minimum requirements for through model
classes are:

   - one ``ForeignKey`` to the source model
   - one ``GenericForeignKey`` with its ``ForeignKey`` and ``CharField``

For example::

   class User(models.Model):
      preferred_videos = GM2MField(through='PreferredVideos')

   class PreferredVideos(models.Model):
      user = models.ForeignKey(User)
      video = GenericForeignKey(ct_field='video_ct', fk_field='video_fk')
      video_ct = models.ForeignKey(ContentType)
      video_fk = models.CharField(max_length=255)

      ... any relevant field (e.g. date added)


Other parameters
----------------

In addition to the specific ``on_delete*`` and ``through`` parameters, you can
use the following optional keyword arguments when defining a ``GM2MField``.
Most of them have the same signification than in Django.

verbose_name
   A human-readable name for the field. Defaults to a munged version of the
   model class name.

db_table
   The name of the database table to use for the model. Defaults to
   ``'<app_label>_<model_name>'``.

related_name
   The name that will be used for the relation from a related object back to
   this one. The same related name is used for all the related models. Defaults
   to ``'<src_model_name>_set'``.

related_query_name
   The name to use for the reverse filter name from the target model.
   Defaults to the value of ``related_name`` or the name of the model.


Future improvements
-------------------

- Automatic creation of relations when an instance of an unrelated model
  is added to the many-to-many. This implies deletion as well.
- More deletion behavior options (possibility to pass any custom function?)
- Add Django admin and possibly ``limit_choices_to`` support


.. |copyright| unicode:: 0xA9

.. _django-generic-m2m: https://pypi.python.org/pypi/django-generic-m2m
