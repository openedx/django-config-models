"""
Decorators for model-based configuration.
"""
from __future__ import unicode_literals, absolute_import

from functools import wraps
from django.http import HttpResponseNotFound


def require_config(config_model):
    """
    View decorator that enables/disables a view based on configuration.

    Arguments:
        config_model (ConfigurationModel subclass): The class of the configuration
            model to check.

    Returns:
        HttpResponse: 404 if the configuration model is disabled,
            otherwise returns the response from the decorated view.

    """
    def _decorator(func):
        """
        Decorator implementation.
        """
        @wraps(func)
        def _inner(*args, **kwargs):
            """
            Wrapper implementation.
            """
            if not config_model.current().enabled:
                return HttpResponseNotFound()
            else:
                return func(*args, **kwargs)
        return _inner
    return _decorator
