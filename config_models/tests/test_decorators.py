"""
Tests for config models decorators
"""

from __future__ import absolute_import, unicode_literals
from django.utils import six

from config_models import decorators
from config_models.models import ConfigurationModel
from config_models.tests.utils import CacheIsolationTestCase

# pylint: disable=model-missing-unicode
@six.python_2_unicode_compatible
class ExampleDecoratorConfig(ConfigurationModel):
    """
    Test model for testing the require_config decorator
    """
    def __str__(self):
        return "ExampleDecoratorConfig(enabled={})".format(self.enabled)


@decorators.require_config(ExampleDecoratorConfig)
def decorated_fake_view():
    """
    Test function to wrap in our decorator.
    """
    return "success"


class RequireConfigTests(CacheIsolationTestCase):
    """
    Tests the require_config decorator.
    """
    def test_no_config(self):
        self.assertIs(decorators.HttpResponseNotFound, type(decorated_fake_view()))

    def test_config_enabled(self):
        ExampleDecoratorConfig.objects.create(enabled=True)
        self.assertEqual(decorated_fake_view(), "success")

    def test_config_disabled(self):
        ExampleDecoratorConfig.objects.create(enabled=False)
        self.assertIs(decorators.HttpResponseNotFound, type(decorated_fake_view()))
