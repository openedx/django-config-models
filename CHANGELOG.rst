Change Log
----------

..
   All enhancements and patches to django-config-models will be documented
   in this file.  It adheres to the structure of http://keepachangelog.com/ ,
   but in reStructuredText instead of Markdown (for ease of incorporation into
   Sphinx documentation and the PyPI description).

   This project adheres to Semantic Versioning (http://semver.org/).

.. There should always be an "Unreleased" section for changes pending release.

Unreleased
~~~~~~~~~~

[2.2.2] - 2021-20-12
~~~~~~~~~~~~~~~~~~~~
* Updated dependencies after removing unnecessary constraint on edx-django-utils, so the constraint will no longer be advertised.

[2.2.1] - 2021-20-12
~~~~~~~~~~~~~~~~~~~~
* Replaced deprecated 'django.utils.translation.ugettext' with 'django.utils.translation.gettext'

[2.2.0] - 2021-07-14
~~~~~~~~~~~~~~~~~~~~
* Added support for django3.2

[2.1.2] - 2021-06-24
~~~~~~~~~~~~~~~~~~~~
* Move out django pin from base.in. Now it is coming from global constraint. Ran make upgrade.

[2.1.1] - 2021-01-28
~~~~~~~~~~~~~~~~~~~~
* Fix deprecated reference of ``util.memcache.safe_key``

[2.1.0] - 2021-01-12
~~~~~~~~~~~~~~~~~~~~
* Dropped Python 3.5 Support

[2.0.2] - 2020-05-10
~~~~~~~~~~~~~~~~~~~~
* Fix html escaping of edit links in admin

[2.0.1] - 2020-05-08
~~~~~~~~~~~~~~~~~~~~
* Dropped support for Django<2.2
* Dropped support for python3.6
* Added support for python3.8

[2.0.0] - 2020-02-06
~~~~~~~~~~~~~~~~~~~~
* Dropping support for Python 2.7
* Switch to using edx-django-utils TieredCache (a two-layer cache that uses both
  Django's cache and an internal request-level cache) to reduce the number of
  memcached roundtrips. This was a major performance issue that accounted for
  10-20% of transaction time for certain courseware views in edx-platform.
* It is now REQUIRED to add `RequestCacheMiddleware` `to middleware
  <https://github.com/edx/edx-django-utils/tree/master/edx_django_utils/cache#tieredcachemiddleware>`_
  to use ConfigModels.
* Remove usage of the "configuration" cache setting. ConfigModels now always use
  the default Django cache.
* Django Rest Framework 3.7 and 3.8 are no longer supported.

[1.0.1] - 2019-04-23
~~~~~~~~~~~~~~~~~~~~
* Fix auto publishing to PyPI

[1.0.0] - 2019-04-23
~~~~~~~~~~~~~~~~~~~~
Changed
-------
* Unpin django-rest-framework requirements. This is a potentially **breaking change** if people were
  relying on this package to ensure the correct version of djangorestframework was being installed.


[0.2.0] - 2018-07-13
~~~~~~~~~~~~~~~~~~~~

Added
-----
* Support for Python 3.6

Removed
-------
* Testing against Django 1.8 - 1.10

Changed
-------
* Updated dependency management to follow OEP-18

[0.1.10] - 2018-05-21
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Changed
-------
* Don't assume the user model is Django's default auth.User


[0.1.9] - 2017-08-07
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Changed
-------
* Updated Django REST Framework dependency to 3.6 as we were not actually compatible with 3.2.


[0.1.8] - 2017-06-19
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Added
-----
* Support for Django 1.11.


[0.1.7] - 2017-06-19
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* Unreleased version number


[0.1.6] - 2017-06-01
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Added
-----
* Support for Django 1.10.

[0.1.1] - [0.1.5] - 2017-06-01
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Added
_____

* Add quality testing to travis run.
* Add encrypted password for package PyPI.

Removed
-------

* Remove the quality condition on deployment.
* Remove the version combos known to fail.

Changed
-------

* Allow for lower versions of djangorestframework, to be compatible with edx-platform.
* Constrict DRF to version that works.
* Update versions of requirements via pip-compile.
* Use different test target - test-all instead of validate.

Fixed
-----

* Fix name and supported versions.

[0.1.0] - 2016-10-06
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Added
_____

* First release on PyPI.
