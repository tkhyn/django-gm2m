.. _quick-start:

Quick start
===========


Installation
------------

As straightforward as it can be, using ``pip``::

   pip install django-gm2m

You then need to make sure that ``django.contrib.contenttypes`` appears
somewhere in your ``INSTALLED_APPS`` setting, and add ``gm2m`` to it::

   INSTALLED_APPS = [
      ...
      'django.contrib.contenttypes',
      ...
      'gm2m',
   ]


First steps
-----------

You can use the exposed ``GM2MField`` exactly the same way as a
``ManyToManyField``.

Suppose you have some models describing videos types::

   >>> from django.db import models
   >>>
   >>> class Video(models.Model):
   >>>     pass
   >>>
   >>> class Movie(Video):
   >>>     pass
   >>>
   >>> class Documentary(Video):
   >>>     pass

Now, if you want to have a field for the preferred videos of a User, you simply
need to add a default ``GM2MField`` to the ``User`` model::

   >>> from gm2m import GM2MField
   >>>
   >>> class User(models.Model):
   >>>     preferred_videos = GM2MField()

Now you can add videos to the ``preferred_videos`` set::

   >>> user = User.objects.create()
   >>> movie = Movie.objects.create()
   >>>
   >>> user.preferred_videos.add(movie)

or::

   >>> user.preferred_videos = [movie]

You can obviously mix instances from different models::

   >>> documentary = Documentary.objects.create()
   >>> user.preferred_videos = [movie, documentary]

From a ``User`` instance, you can fetch all the user's preferred videos::

   >>> list(user.preferred_videos)
   [<Movie object>, <Documentary object>]

Which you may filter by model using the ``Model`` or ``Model__in`` keywords::

   >>> list(user.preferred_videos.filter(Model=Movie))
   [<Movie object>]
   >>> list(user.preferred_videos.filter(Model__in=[Documentary]))
   [<Documentary object>]

That's it for a basic use of django-gm2m. You may be interested in the more
advanced :ref:`features <features>` it offers.
