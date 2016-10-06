Part of `edX code`__.

__ http://code.edx.org/

django-config-models  |Travis|_ |Codecov|_
===================================================
.. |Travis| image:: https://travis-ci.org/edx/config_models.svg?branch=master
.. _Travis: https://travis-ci.org/edx/config_models

.. |Codecov| image:: http://codecov.io/github/edx/config_models/coverage.svg?branch=master
.. _Codecov: http://codecov.io/github/edx/config_models?branch=master

Overview
--------

This app allows other apps to easily define a configuration model
that can be hooked into the admin site to allow configuration management
with auditing.

Installation
------------

Add ``config_models`` to your ``INSTALLED_APPS`` list.

Usage
-----

Create a subclass of ``ConfigurationModel``, with fields for each
value that needs to be configured::

    class MyConfiguration(ConfigurationModel):
        frobble_timeout = IntField(default=10)
        frazzle_target = TextField(defalut="debug")

This is a normal django model, so it must be synced and migrated as usual.

The default values for the fields in the ``ConfigurationModel`` will be
used if no configuration has yet been created.

Register that class with the Admin site, using the ``ConfigurationAdminModel``::

    from django.contrib import admin

    from config_models.admin import ConfigurationModelAdmin

    admin.site.register(MyConfiguration, ConfigurationModelAdmin)

Use the configuration in your code::

    def my_view(self, request):
        config = MyConfiguration.current()
        fire_the_missiles(config.frazzle_target, timeout=config.frobble_timeout)

Use the admin site to add new configuration entries. The most recently created
entry is considered to be ``current``.

Configuration
-------------

The current ``ConfigurationModel`` will be cached in the ``configuration`` django cache,
or in the ``default`` cache if ``configuration`` doesn't exist. You can specify the cache
timeout in each ``ConfigurationModel`` by setting the ``cache_timeout`` property.

You can change the name of the cache key used by the ``ConfigurationModel`` by overriding
the ``cache_key_name`` function.

Extension
---------

``ConfigurationModels`` are just django models, so they can be extended with new fields
and migrated as usual. Newly added fields must have default values and should be nullable,
so that rollbacks to old versions of configuration work correctly.

Documentation
-------------

The full documentation is at https://config_models.readthedocs.org.

License
-------

The code in this repository is licensed under the AGPL 3.0 unless
otherwise noted.

Please see ``LICENSE.txt`` for details.

How To Contribute
-----------------

Contributions are very welcome.

Please read `How To Contribute <https://github.com/edx/edx-platform/blob/master/CONTRIBUTING.rst>`_ for details.

Even though they were written with ``edx-platform`` in mind, the guidelines
should be followed for Open edX code in general.

Reporting Security Issues
-------------------------

Please do not report security issues in public. Please email security@edx.org.

Mailing List and IRC Channel
----------------------------

You can discuss this code in the `edx-code Google Group`__ or in the ``#edx-code`` IRC channel on Freenode.

__ https://groups.google.com/forum/#!forum/edx-code
