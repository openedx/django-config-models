from config_models.models import ConfigurationModel
from django.contrib.auth.models import User
from django.conf import settings
from django.db import models
from django.utils import six


# pylint: disable=model-missing-unicode
@six.python_2_unicode_compatible
class ExampleConfig(ConfigurationModel):
    """
    Test model for testing ``ConfigurationModels``.
    """
    cache_timeout = 300

    string_field = models.TextField()
    int_field = models.IntegerField(default=10)

    def __str__(self):
        return "ExampleConfig(enabled={}, string_field={}, int_field={})".format(
            self.enabled, self.string_field, self.int_field
        )


# pylint: disable=model-missing-unicode
@six.python_2_unicode_compatible
class ManyToManyExampleConfig(ConfigurationModel):
    """
    Test model configuration with a many-to-many field.
    """
    cache_timeout = 300

    string_field = models.TextField()
    many_user_field = models.ManyToManyField(User, related_name='topic_many_user_field')

    def __str__(self):
        return "ManyToManyExampleConfig(enabled={}, string_field={})".format(self.enabled, self.string_field)

# pylint: disable=model-missing-unicode
@six.python_2_unicode_compatible
class ExampleKeyedConfig(ConfigurationModel):
    """
    Test model for testing ``ConfigurationModels`` with keyed configuration.

    Does not inherit from ExampleConfig due to how Django handles model inheritance.
    """
    cache_timeout = 300

    KEY_FIELDS = ('left', 'right', 'user')

    left = models.CharField(max_length=30)
    right = models.CharField(max_length=30)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='test_user')

    string_field = models.TextField()
    int_field = models.IntegerField(default=10)

    def __str__(self):
        return "ExampleKeyedConfig(enabled={}, left={}, right={}, user={}, string_field={}, int_field={})".format(
            self.enabled, self.left, self.right, self.user, self.string_field, self.int_field
        )


# pylint: disable=model-missing-unicode
@six.python_2_unicode_compatible
class ExampleDecoratorConfig(ConfigurationModel):
    """
    Test model for testing the require_config decorator
    """
    def __str__(self):
        return "ExampleDecoratorConfig(enabled={})".format(self.enabled)


# pylint: disable=model-missing-unicode
@six.python_2_unicode_compatible
class ExampleDeserializeConfig(ConfigurationModel):
    """
    Test model for testing deserialization of ``ConfigurationModels`` with keyed configuration.
    """
    KEY_FIELDS = ('name',)

    name = models.TextField()
    int_field = models.IntegerField(default=10)

    def __str__(self):
        return "ExampleDeserializeConfig(enabled={}, name={}, int_field={})".format(
            self.enabled, self.name, self.int_field
        )
