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
   >>>     title = models.CharField(max_length=255)
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
   >>>     name = models.CharField(max_length=255)
   >>>     preferred_videos = GM2MField()

Now you can add videos to the ``preferred_videos`` set::

   >>> me = User.objects.create(name='Me')
   >>> v_for_vendetta = Movie.objects.create(title='V for Vendetta')
   >>>
   >>> me.preferred_videos.add(v_for_vendetta)

or::

   >>> user.preferred_videos = [v_for_vendetta]

You can obviously mix instances from different models::

   >>> citizenfour = Documentary.objects.create(title='Citizenfour')
   >>> user.preferred_videos = [v_for_vendetta, citizenfour]

From a ``User`` instance, you can fetch all the user's preferred videos::

   >>> [v.title for v in me.preferred_videos]
   ['V for Vendetta', 'Citizenfour']

... which you may filter by model using the ``Model`` or ``Model__in``
keywords::

   >>> [v.title for v in me.preferred_videos.filter(Model=Movie)]
   ['V for Vendetta']
   >>> [v.title for v in me.preferred_videos.filter(Model__in=[Documentary])]
   ['Citizenfour']

That's it regarding the basic usage of ``django-gm2m``. You'll probably want to
have a look at the more advanced :ref:`features <features>` it offers.
