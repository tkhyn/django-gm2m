django-gm2m tests
=================

If you are reading this, you're interested in contributing to django-gm2m.
Great news!

Before you start playing around, you may need the information that follows,
especially if you're not familiar with zc.buildout and/or tox.


The tests
---------

django-gm2m uses pytest_django_ for testing. All the test modules are
contained in individual dummy Django apps in the ``tests`` directory. The test
modules are named ``tests*.py`` so that pytest can discover them, and the test
classes are subclasses of ``tests._TestCase`` so that when running
tests in an app, the app is automatically enabled and the associated models
defined in ``models.py`` are created. After the tests for that app have
finished, the app is disabled and the models are destroyed for the next app.

The ``tests.app`` app is always enabled and contains some base models. No test
should be written in this app.

A test class can install other apps during its test by using the ``other_apps``
class attribute, which is an empty tuple by default.

The ``setup.cfg`` file contains coverage pre-configuration information,
but coverage is disabled by default.

Using buildout
--------------

django-gm2m uses zc.buildout_ to generate tests scripts. In (very) short
if you have never heard of it, zc.buildout is a tool to assemble given
versions of libraries together in completely isolated virtual environments,
ensuring robustness and repeatability. Its most common usage is to generate
scripts or builds.

You don't even need to install it globally nor in a virtual environment as it
has its own local installation script. To locally install buildout, go to the
main directory (where the ``buildout.cfg`` and ``bootstrap.py`` lie),
and type::

   $ python bootstrap.py

This will create a ``buildout`` script in a ``bin`` folder. Now you just have
to run::

   $ bin/buildout

It may take a few minutes to download and install the dependencies in the
*local* folder, and generate the scripts as defined in the ``buildout.cfg``
file.

You'll end up with:

bin/python
   An interpreter with all the relevant librairies in ``sys.path``, so that
   you can experiment in the actual environment of the software, with the
   versions that are specified in the buildout configuration and that are
   used for the tests.

bin/tests
   This script runs the test suite. See below, `Running the tests`_.

bin/coverage
   This script runs the test suite and outputs coverage information.

.. tip::
   If you don't want the packages to be downloaded and installed each time
   you run ``buildout`` or each time you change a version in ``buildout.cfg``,
   you may want to consider using a ``~/.buildout/default.cfg`` file to specify
   download and eggs installation paths using the ``download-cache`` and
   ``eggs-directory`` options.


Running the tests
-----------------

Simply generate the ``bin/tests`` script and, from the root directory, type::

   $ bin/tests

For coverage information, you can add ``--with-coverage`` to the above test
command but it's more convenient to use the shortcut::

   $ bin/coverage

You may want to run the test suite manually from the command line (to launch
tests from within an IDE, for example). To do this:

   - make sure that all the required dependencies are satisfied in the
     environment you are working in
   - add the main directory (where ``setup.py`` lies) to ``PYTHONPATH``
   - set the working directory to ``tests``

And simply use::

   $ pytest [options]


Running the tox suite
---------------------

django-gm2m also uses tox_ to test against various environments (mainly
python and django versions).

While buildout is great to test against given versions of libraries with a
given interpreter (the one you used to run ``python bootstrap.py``), tox
focuses on running commands in various environments (the ones the users of the
software will run it in). It basically creates virtual environments and runs
the test suite (possibly with adaptations) in each of these environments.

Running the tox suite is just a matter of installing tox and running it from
the main directory::

   $ pip install tox
   $ tox


.. _pytest_django: https://pytest-django.readthedocs.io/en/latest/
.. _zc.buildout: http://www.buildout.org/en/latest/
.. _tox: https://testrun.org/tox/
