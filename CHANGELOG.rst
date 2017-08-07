Change Log
----------

..
   All enhancements and patches to cookiecutter-django-app will be documented
   in this file.  It adheres to the structure of http://keepachangelog.com/ ,
   but in reStructuredText instead of Markdown (for ease of incorporation into
   Sphinx documentation and the PyPI description).

   This project adheres to Semantic Versioning (http://semver.org/).

.. There should always be an "Unreleased" section for changes pending release.

Unreleased
~~~~~~~~~~

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
