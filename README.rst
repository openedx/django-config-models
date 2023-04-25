django-config-models
********************

|CI|_ |Codecov|_ |pypi-badge| |doc-badge| |pyversions-badge| |license-badge| |status-badge|
===========================================================================================

.. |CI| image:: https://github.com/openedx/django-config-models/workflows/Python%20CI/badge.svg?branch=master
.. _CI: https://github.com/openedx/django-config-models/actions?query=workflow%3A%22Python+CI%22

.. |Codecov| image:: http://codecov.io/github/openedx/django-config-models/coverage.svg?branch=master
.. _Codecov: http://codecov.io/github/openedx/django-config-models?branch=master

.. |pypi-badge| image:: https://img.shields.io/pypi/v/django-config-models.svg
    :target: https://pypi.python.org/pypi/django-config-models/
    :alt: PyPI

.. |doc-badge| image:: https://readthedocs.org/projects/django-config-models/badge/?version=latest
    :target: http://django-config-models.readthedocs.io/en/latest/
    :alt: Documentation

.. |pyversions-badge| image:: https://img.shields.io/pypi/pyversions/django-config-models.svg
    :target: https://pypi.python.org/pypi/django-config-models/
    :alt: Supported Python versions

.. |license-badge| image:: https://img.shields.io/github/license/edx/django-config-models.svg
    :target: https://github.com/openedx/django-config-models/blob/master/LICENSE.txt
    :alt: License

.. |status-badge| image:: https://img.shields.io/badge/Status-Maintained-brightgreen
    :alt: Maintenance status


Purpose
-------

This app allows other apps to easily define a configuration model
that can be hooked into the admin site to allow configuration management
with auditing.

Getting Started
---------------

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
or in the ``default`` cache if ``configuration`` doesn't exist. The ``configuration`` and ``default`` caches
are specified in the django ``CACHES`` setting. The caching can be per-process, per-machine, per-cluster, or
some other strategy, depending on the cache configuration.

You can specify the cache timeout in each ``ConfigurationModel`` by setting the ``cache_timeout`` property.

You can change the name of the cache key used by the ``ConfigurationModel`` by overriding
the ``cache_key_name`` function.

Extension
---------

``ConfigurationModels`` are just django models, so they can be extended with new fields
and migrated as usual. Newly added fields must have default values and should be nullable,
so that rollbacks to old versions of configuration work correctly.

Documentation
-------------

The full documentation is at https://django-config-models.readthedocs.org.

License
-------

The code in this repository is licensed under the AGPL 3.0 unless
otherwise noted.

Please see ``LICENSE.txt`` for details.

Getting Help
------------

If you're having trouble, we have discussion forums at
`discuss.openedx.org <https://discuss.openedx.org>`_ where you can connect with others in the
community.

Our real-time conversations are on Slack. You can request a `Slack
invitation`_, then join our `community Slack workspace`_.

For anything non-trivial, the best path is to `open an issue`__ in this
repository with as many details about the issue you are facing as you
can provide.

__ https://github.com/openedx/django-config-models /issues

For more information about these options, see the `Getting Help`_ page.

.. _Slack invitation: https://openedx.org/slack
.. _community Slack workspace: https://openedx.slack.com/
.. _Getting Help: https://openedx.org/getting-help

How To Contribute
-----------------

Contributions are very welcome.

Please read `How To Contribute <https://github.com/openedx/.github/blob/master/CONTRIBUTING.md>`_ for details.


This project is currently accepting all types of contributions, bug fixes, security fixes, maintenance work, or new features. However, please make sure to have a discussion about your new feature idea with the maintainers prior to beginning development to maximize the chances of your change being accepted. You can start a conversation by creating a new issue on this repo summarizing your idea.

Open edX Code of Conduct
------------------------
All community members are expected to follow the `Open edX Code of Conduct`_.

.. _Open edX Code of Conduct: https://openedx.org/code-of-conduct/

People
------
The assigned maintainers for this component and other project details may be
found in `Backstage`_. Backstage pulls this data from the ``catalog-info.yaml``
file in this repo.

.. _Backstage: https://backstage.openedx.org/catalog/default/component/django-config-models

Reporting Security Issues
-------------------------

Please do not report security issues in public. Please email security@edx.org.
